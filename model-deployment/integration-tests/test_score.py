import logging
import math
import os
import subprocess
import sys

import boto3
import pandas as pd
from pandas import Timestamp

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566/")
BUCKET_NAME = os.getenv("BUCKET_NAME", "bike-duration")
INPUT_FILE_PATTERN = os.getenv("INPUT_FILE_PATTERN")
OUTPUT_FILE_PATTERN = os.getenv("OUTPUT_FILE_PATTERN")

os.environ["AWS_ACCESS_KEY_ID"] = "ABCDEF"
os.environ["AWS_SECRET_ACCESS_KEY"] = "UVWXYZ"
logging.basicConfig(level=logging.INFO)


def test_processing_features(year: int, month: int):
    """Test processing features"""

    data = [
        {
            'SL_EL': '31223_31035',
            'day_of_week': 'Tuesday',
            'distance': 0.8144372166017364,
            'end_lat': 38.876393,
            'end_lng': -77.107735,
            'end_station_id': 31035,
            'ended_at': Timestamp('2022-03-15 18:17:02'),
            'member_casual': 'member',
            'rideable_type': 'classic_bike',
            'start_hour': 18,
            'start_lat': 38.882788,
            'start_lng': -77.103148,
            'start_station_id': 31223,
            'started_at': Timestamp('2022-03-15 18:00:08'),
        },
        {
            'SL_EL': '31223_31035',
            'day_of_week': 'Sunday',
            'distance': 0.8144372166017364,
            'end_lat': 38.876393,
            'end_lng': -77.107735,
            'end_station_id': 31035,
            'ended_at': Timestamp('2022-03-20 18:25:28'),
            'member_casual': 'causal',
            'rideable_type': 'classic_bike',
            'start_hour': 18,
            'start_lat': 38.882788,
            'start_lng': -77.103148,
            'start_station_id': 31223,
            'started_at': Timestamp('2022-03-20 18:19:43'),
        },
        {
            'SL_EL': '31223_31624',
            'day_of_week': 'Wednesday',
            'distance': 0.7620865627773037,
            'end_lat': 38.897446,
            'end_lng': -77.009888,
            'end_station_id': 31624,
            'ended_at': Timestamp('2022-03-16 12:48:00'),
            'member_casual': 'member',
            'rideable_type': 'electric_bike',
            'start_hour': 12,
            'start_lat': 38.900412,
            'start_lng': -77.001949,
            'start_station_id': 31223,
            'started_at': Timestamp('2022-03-16 12:44:09'),
        },
    ]

    columns = [
        "SL_EL",
        "day_of_week",
        "distance",
        "end_lat",
        "end_lng",
        "end_station_id",
        "ended_at",
        "member_casual",
        "rideable_type",
        "start_hour",
        "start_lat",
        "start_lng",
        "start_station_id",
        "started_at",
    ]

    df = pd.DataFrame(data=data, columns=columns)

    options = {'client_kwargs': {'endpoint_url': S3_ENDPOINT_URL}}

    input_file = INPUT_FILE_PATTERN.format(year=year, month=month)

    df.to_parquet(
        input_file, engine='pyarrow', compression=None, index=False, storage_options=options
    )

    client = boto3.client('s3', endpoint_url=S3_ENDPOINT_URL)

    # Check if file as been created as intended in the bucket
    response = client.head_object(
        Bucket=BUCKET_NAME, Key='in/{year:04d}-{month:02d}.parquet'.format(year=year, month=month)
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_save_data(year, month):
    """Test function to make sure file is processed and saved in S3"""

    subprocess.run(['python ../prefect_deployment/score.py %s %s' % (year, month)], shell=True)
    client = boto3.client('s3', endpoint_url=S3_ENDPOINT_URL)

    # Check if file as been created as intended in the bucket
    year = int(year)
    month = int(month)
    response = client.head_object(
        Bucket=BUCKET_NAME, Key='out/{year:04d}-{month:02d}.parquet'.format(year=year, month=month)
    )
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_output_predictions(year, month):
    """Test predictions of the output file"""

    options = {'client_kwargs': {'endpoint_url': S3_ENDPOINT_URL}}

    output_file = OUTPUT_FILE_PATTERN.format(year=year, month=month)

    df = pd.read_parquet(output_file, storage_options=options)
    output_result = df["predictions"].sum()
    expected_result = 20.204903

    assert math.isclose(expected_result, output_result, abs_tol=0.001)


def run_integration_tests(year, month):
    """Run integration tests"""

    test_processing_features(year=year, month=month)
    test_save_data(year=year, month=month)
    test_output_predictions(year=year, month=month)


if __name__ == "__main__":

    year = int(sys.argv[1])
    month = int(sys.argv[2])

    logging.info("Running integration tests")

    run_integration_tests(year=year, month=month)
