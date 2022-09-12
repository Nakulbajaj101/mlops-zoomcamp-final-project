from datetime import datetime

import haversine as hs
import pandas as pd


def get_distance_kilometres(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> hs.haversine:
    """Calculate distance in kilometres"""

    start_loc=(start_lat, start_lon)
    end_loc=(end_lat, end_lon)
    return hs.haversine(start_loc, end_loc, unit=hs.Unit.KILOMETERS)


def preprocess_data(df: pd.DataFrame, target_column: str="duration") -> pd.DataFrame:
    """Creating new features"""

    data = df.copy()
    date_fields = ["started_at", "ended_at"]
    for cols in date_fields:
        if data[cols].dtype == 'O': 
            data[cols] = [datetime.strptime(val, '%Y-%m-%d %H:%M:%S') for val in data[cols]]
    data[target_column] = (data["ended_at"] - data["started_at"]).apply(lambda x: x.total_seconds()/60)
    data = data[(data[target_column] > 0) & (data[target_column] <= 120)].dropna(axis=0).copy()
    data["distance"] = [get_distance_kilometres(start_lat, start_lng, end_lat, end_lng)
                        for start_lat, start_lng, end_lat, end_lng in 
                        zip(data["start_lat"], data["start_lng"], data["end_lat"], data["end_lng"])]
    data["SL_EL"] = data["start_station_id"].astype(int).astype(str) + "_" + data["end_station_id"].astype(int).astype(str)
    data["start_hour"] = data["started_at"].dt.hour
    data["day_of_week"] = data["started_at"].dt.day_name()
    return data
