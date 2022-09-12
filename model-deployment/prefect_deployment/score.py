import os
import pathlib
import pickle
import shutil
import sys
import uuid
import zipfile
from datetime import datetime

import haversine as hs
import mlflow
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from mlflow.tracking import MlflowClient
from prefect import flow, get_run_logger, task
from prefect.context import get_run_context
from tqdm import tqdm

model_name = "bikeshare-model"
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", None)
FILEPATH = pathlib.Path(__file__).parent.resolve()

if not S3_ENDPOINT_URL:
    mlflow.set_tracking_uri(uri='http://127.0.0.1:5000')


def load_model():
    """Load model from mlflow server"""

    if not S3_ENDPOINT_URL:
        model_uri = f"models:/{model_name}/Production"
    else:
        model_uri = os.path.join(FILEPATH, 'model')
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    return model


def get_run_id():
    """Get model run id"""

    client = MlflowClient()
    model_metadata = client.get_latest_versions(name=model_name, stages=["Production"])[0]
    run_id = model_metadata.run_id

    return run_id


def load_preprocessor(logger: get_run_logger = None):
    """Load preprocessor"""

    models_dir = os.path.join(FILEPATH, 'preprocessor')
    transformer_local_path = models_dir + "/transformer.bin"

    if not S3_ENDPOINT_URL:
        client = MlflowClient()
        model_metadata = client.get_latest_versions(name=model_name, stages=["Production"])[0]
        transformer_path = (
            model_metadata.source.split('artifacts/model')[0]
            + "artifacts/preprocessor/transformer.bin"
        )
        logger.info(f"artifacts path: {transformer_path}")
        mlflow.mlflow.artifacts.download_artifacts(artifact_uri=transformer_path, dst_path=models_dir)

    with open(transformer_local_path, 'rb') as file_in:
        transformer = pickle.load(file_in)

    return transformer


def get_distance_kilometres(start_lat, start_lon, end_lat, end_lon):
    """Calculate distance in kilometres"""

    start_loc = (start_lat, start_lon)
    end_loc = (end_lat, end_lon)
    return hs.haversine(start_loc, end_loc, unit=hs.Unit.KILOMETERS)


@task(retries=2)
def process_features(df: pd.DataFrame):
    """Function to process features"""

    data = df.dropna(axis=0).copy()
    date_fields = ["started_at", "ended_at"]
    for cols in date_fields:
        if data[cols].dtype == 'O':
            data[cols] = [datetime.strptime(val, '%Y-%m-%d %H:%M:%S') for val in data[cols]]
    data["distance"] = [
        get_distance_kilometres(start_lat, start_lng, end_lat, end_lng)
        for start_lat, start_lng, end_lat, end_lng in zip(
            data["start_lat"], data["start_lng"], data["end_lat"], data["end_lng"]
        )
    ]
    data["SL_EL"] = (
        data["start_station_id"].astype(int).astype(str)
        + "_"
        + data["end_station_id"].astype(int).astype(str)
    )
    data["start_hour"] = data["started_at"].dt.hour
    data["day_of_week"] = data["started_at"].dt.day_name()

    return data


@task(retries=2)
def score_data(df_processed: pd.DataFrame, logger: get_run_logger = None):
    """Function to predict bike ride share rentals"""

    data_processed = df_processed.copy()
    preprocessor = load_preprocessor(logger=logger)
    feature_cols = [
        "rideable_type",
        "distance",
        "member_casual",
        "SL_EL",
        "day_of_week",
        "start_hour",
    ]

    logger.info("Transforming ride data")
    X = preprocessor.transform(data_processed[feature_cols].to_dict(orient="records"))

    logger.info("Loading model")
    model = load_model()

    logger.info("Making predictions")
    predictions = model.predict(X)

    data_processed["predictions"] = predictions
    data_processed["ride_id"] = [str(uuid.uuid4()) for val in data_processed.index]
    if not S3_ENDPOINT_URL:
        run_id = get_run_id()
    else:
        run_id = model.metadata.to_dict()['run_id']

    data_processed["run_id"] = run_id
    data_processed["scored_time"] = datetime.now()

    logger.info("Rides scoring completed")

    return data_processed


@task(retries=2)
def get_output_path(year, month):
    """Function to create output path based on year and month"""

    default_output_pattern = 's3://bikeshare-scored-data-stage/bikeshare/year={year:04d}/month={month:02d}/predictions.parquet'
    output_pattern = os.getenv('OUTPUT_FILE_PATTERN', default_output_pattern)
    return output_pattern.format(year=year, month=month)


@task(retries=2)
def output_data(output_file: str = "", output_data: pd.DataFrame = None):
    """Function to output data to s3"""

    df = output_data.copy()
    if S3_ENDPOINT_URL:
        options = {'client_kwargs': {'endpoint_url': S3_ENDPOINT_URL}}
        df.to_parquet(
            output_file, engine='pyarrow', compression=None, index=False, storage_options=options
        )
    else:
        df.to_parquet(output_file, engine='pyarrow', index=False)


def download_data(destination_dir: str = "", filename: str = ""):
    """Function to get data from the s3"""

    # Change the url based on what works for you whether s3 or cloudfront
    destination_dir = os.path.join(FILEPATH, destination_dir)
    if not os.path.exists(destination_dir):
        os.mkdir(destination_dir)
    url = f"https://s3.amazonaws.com/capitalbikeshare-data/{filename}"
    resp = requests.get(url, stream=False)
    save_path = f"{destination_dir}/{filename}"
    with open(save_path, "wb") as handle:
        for data in tqdm(
            resp.iter_content(),
            desc=f"{filename}",
            postfix=f"save to {save_path}",
            total=int(resp.headers["Content-Length"]),
        ):
            handle.write(data)

    # Extract zip files
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)

    # Remove zip files
    os.remove(save_path)


@task(retries=2)
def get_file_path(destination_dir: str = "", filename: str = "", logger: get_run_logger = None):
    """Function to get file path"""

    file = filename.split(".")[0] + ".csv"
    filepath = os.path.join(FILEPATH, destination_dir + "/" + file)
    input_filepath = os.getenv('INPUT_FILE_PATTERN', filepath)
    logger.info(f"{input_filepath}")
    if "s3://" in input_filepath:
        logger.info(f"File {filename} already exists in S3, no need to download")
        return input_filepath

    elif input_filepath and os.path.exists(input_filepath):
        logger.info(f"File {filename} already exists in local dir, no need to download")
        return input_filepath

    else:
        logger.info(f"File {filename} doesnt exists, downloading")
        download_data(destination_dir=destination_dir, filename=filename)

        return input_filepath


@task(retries=2)
def get_year_month(date: datetime):
    """Get year month for scoring data"""

    relative_date = date - relativedelta(months=1)

    year = relative_date.year
    month = relative_date.month

    return year, month


@flow(name="bikeshare-rental-batch-score")
def batch_score(date: datetime = None):
    """Main python function that runs the script"""

    logger = get_run_logger()
    run_date = ''
    if date is None:
        ctx = get_run_context()
        run_date = ctx.flow_run.expected_start_time
    else:
        run_date = date

    year, month = get_year_month(date=run_date)
    logger.info(f"Year is {year} and month is {month} for scoring data")

    input_file = f"{year}{str(month).zfill(2)}-capitalbikeshare-tripdata.zip"
    destination_dir = "datasets"

    if not os.path.exists(os.path.join(FILEPATH, destination_dir)):
        os.makedirs(os.path.join(FILEPATH, destination_dir))

    input_path = get_file_path(destination_dir=destination_dir, filename=input_file, logger=logger)
    if os.getenv('OUTPUT_FILE_PATTERN'):
        output_path = get_output_path(year=run_date.year, month=run_date.month)
    else:
        output_path = get_output_path(year=year, month=month)

    logger.info("Reading the input data")

    if '.csv' in input_path:
        logger.info(f"Data will be read from {input_path}")
        bike_data = pd.read_csv(input_path)
        logger.info("Preprocessing the input data")
        processed_data = process_features(bike_data)

    elif '.parquet' in input_path:
        if S3_ENDPOINT_URL:
            options = {'client_kwargs': {'endpoint_url': S3_ENDPOINT_URL}}
            logger.info(
                f"Data will be read from {input_path.format(year=run_date.year, month=run_date.month)}"
            )
            logger.info(input_path.format(year=run_date.year, month=run_date.month))
            bike_data = pd.read_parquet(
                input_path.format(year=run_date.year, month=run_date.month), storage_options=options
            )
        else:
            bike_data = pd.read_parquet(input_path)
        processed_data = bike_data.copy()

    logger.info("Scoring the bike data")
    score_bike_data = score_data(df_processed=processed_data, logger=logger)

    logger.info("Outputting the scoring data to S3")
    logger.info(f"Predictions will be written to {output_path}")
    output_data(output_file=output_path, output_data=score_bike_data)

    logger.info(f"Cleaning the {destination_dir} folder")
    shutil.rmtree(path=destination_dir, ignore_errors=True)


def run():
    """Function to run the flow if nothing is provided"""

    year = int(sys.argv[1])
    month = int(sys.argv[2])

    date = datetime(year=year, month=month, day=1)
    batch_score(date=date)


if __name__ == "__main__":
    run()
