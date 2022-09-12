import pandas as pd
from pandas import Timestamp

from prefect_deployment.score import get_distance_kilometres, process_features


def test_calculate_distance():
    """Test distance works"""

    start_lat = 38.927095
    start_lng = -76.978924
    end_lat = 38.932456900063606
    end_lng = -76.99353396892548

    distance = get_distance_kilometres(
        start_lat=start_lat, start_lon=start_lng, end_lat=end_lat, end_lon=end_lng
    )
    assert distance == 1.3973505633766143


def test_processing_features():
    """Test processing features"""

    data = [
        [
            '2022-03-15 18:00:08',
            '2022-03-15 18:17:02',
            31223,
            31035,
            38.882788,
            -77.103148,
            38.876393,
            -77.107735,
            'classic_bike',
            'member',
        ],
        [
            '2022-03-20 18:19:43',
            '2022-03-20 18:25:28',
            31223,
            31035,
            38.882788,
            -77.103148,
            38.876393,
            -77.107735,
            'classic_bike',
            'causal',
        ],
        [
            '2022-03-16 12:44:09',
            '2022-03-16 12:48:00',
            31223,
            31624,
            38.900412,
            -77.001949,
            38.897446,
            -77.009888,
            'electric_bike',
            'member',
        ],
    ]
    columns = [
        "started_at",
        "ended_at",
        "start_station_id",
        "end_station_id",
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
        "rideable_type",
        "member_casual",
    ]

    df = pd.DataFrame(data=data, columns=columns)
    result_output = process_features.fn(df).to_dict(orient='records')
    expected_output = [
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
    assert expected_output == result_output
