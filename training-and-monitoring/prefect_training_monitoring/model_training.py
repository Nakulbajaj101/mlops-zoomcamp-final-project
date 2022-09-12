import os
import pickle
import time
from datetime import datetime

import mlflow
import pandas as pd
import xgboost as xgb
from dateutil.relativedelta import relativedelta
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient
from prefect import flow, get_run_logger, task
from prefect.context import get_run_context
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from preprocessors import preprocess_data
from utility_functions import download_data, get_run_id

training_date = datetime.now().strftime('%Y-%m-%d')
tracking_uri="http://127.0.0.1:5000"
train_experiment_name=f"capital-bikeshare-experiment-{training_date}"
test_experiment_name=f"capital-bikeshare-experiment-test-{training_date}"
model_name="bikeshare-model"
mlflow.set_tracking_uri(tracking_uri)



@task(retries=2)
def read_and_process(filepath: str="") -> pd.DataFrame:
    """Function to read and process data"""

    data = pd.read_csv(filepath_or_buffer=filepath)
    processed_data = preprocess_data(df=data, target_column="duration")

    return processed_data


# Data transformation
def transform_train_and_val_data(training_data: pd.DataFrame, valid_data: pd.DataFrame, feature_cols: list=[], target: str=""):
    """Preprocessing data before pass it to the model"""
    
    # Creating preprocessor pipeline
    preprocessor_pipeline = Pipeline(
        steps=[
            ("dict_vectorizor", DictVectorizer()),
            ("scaler", StandardScaler(with_mean=False))
        ]
    )
    X_train = preprocessor_pipeline.fit_transform(training_data[feature_cols].to_dict(orient="records"))
    
    # Writing and storing the preprocessor
    with open("models/transformer.bin", 'wb') as fileout:
        pickle.dump(preprocessor_pipeline, fileout)

    X_val = preprocessor_pipeline.transform(valid_data[feature_cols].to_dict(orient="records")) 

    y_train = training_data[target]
    y_val = valid_data[target]
    train = xgb.DMatrix(X_train, label=y_train)
    valid = xgb.DMatrix(X_val, label=y_val)

    return train, valid, y_val


@task(retries=2)
def tranform_data(data: pd.DataFrame, feature_cols: list=[]):
    """Function to transform data"""

    with open("models/transformer.bin", 'rb') as file:
        transformer = pickle.load(file)

    transformed_data = transformer.transform(data[feature_cols].to_dict(orient="records"))
    return transformed_data


# Hyperoptimisation
@task(retries=2)
def hpo(train: xgb.DMatrix, valid: xgb.DMatrix, y_val: pd.Series, experiment_name: str):
    """Function to train the model"""

    mlflow.set_experiment(experiment_name)

    search_space = {
        'max_depth': scope.int(hp.quniform('max_depth', 4, 100, 1)),
        'learning_rate': hp.loguniform('learning_rate', -3, 0),
        'reg_alpha': hp.loguniform('reg_alpha', -6, 1),
        'reg_lambda': hp.loguniform('reg_lambda', -5, 1),
        'min_child_weight': hp.loguniform('min_child_weight', -1, 3),
        'objective' : 'reg:squarederror',
        'seed': 42
    }

    def objective(params):
    
        with mlflow.start_run():
            mlflow.set_tag("model", "xgboost")
            mlflow.log_params(params)
            model = xgb.train(
                params = params,
                dtrain = train,
                num_boost_round = 120,
                evals = [(valid, "validation")],
                early_stopping_rounds = 20
            )

            y_pred = model.predict(valid)
            val_rmse = mean_squared_error(y_val, y_pred, squared=False)
            mlflow.log_metric("val_rmse", val_rmse)

        return {'loss': val_rmse, 'status': STATUS_OK}

    fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=20,
        trials=Trials()
        )

def train_model(train: xgb.DMatrix, valid: xgb.DMatrix, test: xgb.DMatrix, y_test: pd.Series, params: dict, experiment_name: str=""):
    """Training the final model"""

    mlflow.set_experiment(experiment_name=experiment_name)
    params['max_depth'] = int(params['max_depth'])

    with mlflow.start_run():
        mlflow.set_tag("model", "xgboost")
        mlflow.log_params(params)
        model = xgb.train(
                params = params,
                dtrain = train,
                num_boost_round = 120,
                evals = [(valid, "validation")],
                early_stopping_rounds = 20
            )

        y_pred = model.predict(test)
        rmse = mean_squared_error(y_test, y_pred, squared=False)
        mlflow.log_metric("test_rmse", rmse)
        mlflow.log_artifact(local_path="models/transformer.bin",
                            artifact_path="preprocessor")
        mlflow.xgboost.log_model(xgb_model=model,artifact_path="model")


@task(retries=2)
def validation_run(train: xgb.DMatrix, 
                   valid: xgb.DMatrix,
                   test: xgb.DMatrix,
                   y_test: pd.Series,
                   top_runs: int=5,
                   train_experiment_name: str="",
                   val_experiment_name: str="", 
                   tracking_uri: str=""):
    """Function to train the validation model and evaluate on test"""

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(name=train_experiment_name)


    runs = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=top_runs,
        order_by=["metrics.val_rmse"]
    )

    for run in runs:
        params = run.to_dictionary()["data"]["params"]
        train_model(train=train,
                    valid=valid,
                    test=test,
                    y_test=y_test,
                    params=params,
                    experiment_name=val_experiment_name)


@task(retries=2)
def register_model_prod(experiment_name: str="", model_name: str="", tracking_uri: str="", logger: get_run_logger=None):
    """Register best model"""

    client = MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(name=experiment_name)


    runs = client.search_runs(
        experiment_ids=experiment.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.test_rmse"]
    )

    best_run_id = [run.to_dictionary()["info"]["run_id"] for run  in runs][0]

    # register the best model
    model_uri = f"runs:/{best_run_id}/model"
    mlflow.register_model(model_uri=model_uri, name=model_name)

    logger.info("Registering the model")
    time.sleep(10) # give time for model to register


    logger.info("Transitioning latest model to prod")
    versions = client.get_latest_versions(name=model_name, stages=None)
    for vs in versions:
        client.transition_model_version_stage(
        name=model_name,
        version=vs.version,
        stage="Production"
        )


@task(retries=2)
def add_data_versioning(training_data_file: str="", val_data_file: str="", test_data_file: str="") -> None:
    """Function to add data versioning to prod run"""

    client = MlflowClient()
    model_metadata = client.get_latest_versions(name=model_name, stages=["Production"])[0]
    run_id = model_metadata.run_id

    client.log_param(run_id=run_id, key="training_data", value=training_data_file)
    client.log_param(run_id=run_id, key="validation_data", value=val_data_file)
    client.log_param(run_id=run_id, key="testing_data", value=test_data_file)



@task(retries=2)
def get_file_names(date: str=None):
    """Function to get s3 file paths based on date"""

    file_suffix = "capitalbikeshare-tripdata"
    processed_date = ""
    if not date:
        processed_date = datetime.today()
    else:
        processed_date = date
    train_date = processed_date - relativedelta(months=2)
    val_date = processed_date - relativedelta(months=1)
    test_date = processed_date
    file_extension = ".zip"
    train_path = f"{train_date.year}{str(train_date.month).zfill(2)}-{file_suffix}{file_extension}"
    val_path = f"{val_date.year}{str(val_date.month).zfill(2)}-{file_suffix}{file_extension}"
    test_path = f"{test_date.year}{str(test_date.month).zfill(2)}-{file_suffix}{file_extension}"
    return train_path, val_path, test_path


@task(retries=2)
def get_file_path(destination_dir: str="", filename: str="", logger: get_run_logger=None):
    """Function to get file path"""

    file = filename.split(".")[0] + ".csv"
    filepath = destination_dir + "/" + file
    if os.path.exists(filepath):
        logger.info(f"File {filename} already exists, no need to download")
        return filepath
    
    else:
        logger.info(f"File {filename} doesnt exists, downloading")
        download_data(destination_dir=destination_dir, filename=filename)
        return filepath


@task(retries=2)
def get_training_base_date(run_id: str='', logger: get_run_logger=None) -> datetime:
    """Function to get new base date for training new model"""

    client = MlflowClient()
    params = client.get_run(run_id=run_id).to_dictionary()['data']['params']
    testing_data_file = params['testing_data']
    testing_data_year_month = testing_data_file.split('-')[0]

    logger.info(f"Prod model testing dataset year_month value if {testing_data_year_month}")
    base_date = datetime.strptime(testing_data_year_month, '%Y%m') + relativedelta(months=1)
    return base_date


@flow(name="bikeshare_model_training")
def model_training(date: datetime=None, retraining: bool=False):
    """Running the pipeline"""

    base_date=''
    if date is None:
        ctx = get_run_context()
        base_date = ctx.flow_run.expected_start_time
    else:
        base_date = date

    
    file_destination = "datasets"
    logger = get_run_logger()
    logger.info(f"Base date for training the model is {base_date.strftime('%Y-%m-%d')}")
    if retraining:
        prod_run_id = get_run_id(tracking_uri=tracking_uri, model_name=model_name)
        base_date = get_training_base_date(run_id=prod_run_id, logger=logger)
        logger.info(f"New base date for training the model will be {base_date.strftime('%Y-%m-%d')}")

    logger.info("Getting cloud data path")
    train_loc, validation_loc, testing_loc = get_file_names(date=base_date)
    

    train_data_path = get_file_path(filename=train_loc, destination_dir=file_destination, logger=logger)
    logger.info(f"Train data path is : {train_data_path}")
    val_data_path = get_file_path(filename=validation_loc, destination_dir=file_destination, logger=logger)
    logger.info(f"Val data path is : {val_data_path}")
    test_data_path = get_file_path(filename=testing_loc, destination_dir=file_destination, logger=logger)
    logger.info(f"Test data path is : {test_data_path}")

    logger.info("Processing training and validation data")
    train_data = read_and_process(filepath=train_data_path)
    valid_data = read_and_process(filepath=val_data_path)
    test_data = read_and_process(filepath=test_data_path)
    feature_cols = ["rideable_type", "distance", "member_casual", "SL_EL", "day_of_week", "start_hour"]
    target = "duration"

    # Transforming training and validation data
    logger.info("Transforming training and validation data")
    train, valid, y_val = transform_train_and_val_data(training_data=train_data,
                                                       valid_data=valid_data,
                                                       feature_cols=feature_cols,
                                                       target=target)
    
    # Training the models and performing hyperoptimisation
    logger.info("Running hyperopt with xgboost")
    hpo(train=train, valid=valid, y_val=y_val, experiment_name=train_experiment_name)
    
    # Validate the best models with test set
    logger.info("Getting the best models on validation and scoring on test data")
    transformed_test_data = tranform_data(data=test_data, feature_cols=feature_cols)
    y_test = test_data[target]
    test = xgb.DMatrix(transformed_test_data, y_test)

    validation_run(train=train,
                   valid=valid,
                   test=test,
                   y_test=y_test,
                   top_runs=5,
                   train_experiment_name=train_experiment_name,
                   val_experiment_name=test_experiment_name,
                   tracking_uri=tracking_uri)

    logger.info("Registering the best model that performed best on test set")
    
    register_model_prod(experiment_name=test_experiment_name,
                   model_name=model_name,
                   tracking_uri=tracking_uri,
                   logger=logger)

    logger.info("Adding versioning to the production model run")
    add_data_versioning(training_data_file=train_loc,
                        val_data_file=validation_loc,
                        test_data_file=testing_loc)


def run():
    """Running the flow"""

    year = 2022
    month = 5
    day = 31

    run_date = datetime(year=year, month=month, day=day)
    model_training(date=run_date, retraining=False)


if __name__ == "__main__":
    run()
    