import json
import os
import pickle
from datetime import datetime

import mlflow
import pandas as pd
from dateutil.relativedelta import relativedelta
from evidently import ColumnMapping
from evidently.model_profile import Profile
from evidently.model_profile.sections import (
    DataDriftProfileSection, RegressionPerformanceProfileSection)
from mlflow.tracking import MlflowClient
from prefect import flow, get_run_logger, task
from prefect.context import get_run_context

from model_training import model_training
from preprocessors import preprocess_data
from utility_functions import download_data, get_run_id

model_name = "bikeshare-model"
tracking_uri = "http://127.0.0.1:5000"
mlflow.set_tracking_uri(uri=tracking_uri)


@task(retries=2)
def get_year_month(date: datetime):
    """Get year month for scoring data"""

    relative_date = date - relativedelta(months=1)

    year = relative_date.year
    month = relative_date.month

    return year, month


def load_model():
    """Load model from mlflow server"""

    model_uri = f"models:/{model_name}/Production"
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    return model


@task(retries=2)
def load_preprocessor(logger: get_run_logger=None):
    """Load preprocessor"""

    client = MlflowClient(tracking_uri=tracking_uri)
    models_dir = "./models"
    if not os.path.exists(models_dir):
        os.mkdir(models_dir)
    transformer_local_path = f"{models_dir}/transformer.bin"
    model_metadata = client.get_latest_versions(name=model_name, stages=["Production"])[0]
    transformer_path = model_metadata.source.split('artifacts/model')[0] + "artifacts/preprocessor/transformer.bin"
    logger.info(f"Transformer path is : {transformer_path}")
    mlflow.mlflow.artifacts.download_artifacts(artifact_uri=transformer_path, dst_path=models_dir)

    with open(transformer_local_path, 'rb') as file_in:
        transformer = pickle.load(file_in)

    return transformer

@task(retries=2)
def process_data(filename="", preprocessor=None, model=None):
    """Function to load and process data"""

    data = pd.read_csv(f"{filename}")
    processed_data = preprocess_data(df=data, target_column="target")
    feature_cols = ["rideable_type", "distance", "member_casual", "SL_EL", "day_of_week", "start_hour"]
    X = preprocessor.transform(processed_data[feature_cols].to_dict(orient="records"))
    predictions = model.predict(X)
    processed_data["prediction"] = predictions

    return processed_data


@task(retries=2)
def run_evidently(ref_data, data):
    """Function to run evidently profile"""

    profile = Profile(sections=[DataDriftProfileSection(), RegressionPerformanceProfileSection()])
    mapping = ColumnMapping(prediction="prediction", numerical_features=['distance'],
                            categorical_features=["rideable_type", "member_casual", "start_station_id", "end_station_id", "day_of_week", "start_hour"],
                            datetime_features=[])
    profile.calculate(ref_data, data, mapping)

    report = json.loads(profile.json())

    return report 


@task(retries=2)
def check_drift(report):
    """Function to detect drift"""

    features_drifted = report['data_drift']['data']['metrics']['n_drifted_features']
    features = report['data_drift']['data']['metrics']['n_features']
    dataset_drift = report['data_drift']['data']['metrics']['dataset_drift']
    if (features_drifted/features) > 0.1 or dataset_drift:
        return True
    else:
        return False


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
def get_ref_file_name() -> str:
    """Function to get training reference file from mlflow server"""

    client = MlflowClient()
    run_id = get_run_id(tracking_uri=tracking_uri, model_name=model_name)
    params = client.get_run(run_id=run_id).to_dictionary()['data']['params']
    training_data_file = params['training_data']

    return training_data_file


@flow(name="bikeshare_model_monitoring")
def model_monitoring(date: datetime=None):
    """Monitoring flow"""

    logger = get_run_logger()
    run_date=''
    if date is None:
        ctx = get_run_context()
        run_date = ctx.flow_run.expected_start_time
    else:
        run_date = date

    year, month = get_year_month(date=run_date)
    logger.info(f"Year is {year} and month is {month} for scoring data")

    target_path = "datasets"
    file_suffix = "capitalbikeshare-tripdata"

    logger.info("Getting name of the file to score")
    target_file_name = f"{year}{str(month).zfill(2)}-{file_suffix}.zip"

    logger.info("Getting name of training file")
    ref_data_file_name = get_ref_file_name()

    if not os.path.exists(target_path):
        os.mkdir(target_path)
    
    logger.info(f"Getting the name of downloaded files else downloading")
    scored_data_file = get_file_path(destination_dir=target_path,
                                     filename=target_file_name,
                                     logger=logger)

    ref_data_file = get_file_path(destination_dir=target_path,
                                  filename=ref_data_file_name,
                                  logger=logger)

    logger.info(f"Files used will be {scored_data_file}, {ref_data_file}")

    logger.info("Loading preprocessor and model")
    preprocessor = load_preprocessor(logger=logger)
    model = load_model()

    logger.info("Processing Refernce dataset")
    ref_data = process_data(filename=ref_data_file, model=model, preprocessor=preprocessor)
    
    logger.info("Processing dataset to be scored")
    scored_data = process_data(filename=scored_data_file, model=model, preprocessor=preprocessor)
    
    logger.info("Running evidently report and then detecting drift")
    report = run_evidently(ref_data, scored_data)
    drift = check_drift(report=report)

    if drift:
        logger.info("Run retraining, since features and dataset is drifted")
        model_training(retraining=True)
    else:
        logger.info("No retraining, since not enough evidence of drift")


def run():
    """Function that calls the flow"""

    year=2022
    month=8
    date = datetime(year=year, month=month, day=1)
    model_monitoring(date=date)
    

if __name__ == "__main__":
    run()

