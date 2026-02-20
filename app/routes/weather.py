from fastapi import APIRouter, Depends, Query, Security
from typing import List, Dict, Any
from app.schemas import WeatherPoint
from app.influx import query as influx_query
from app.config import INFLUXDB_BUCKET, INFLUXDB_MEASUREMENT as meas
from app.routes.auth import get_firebase_admin_user

router = APIRouter(prefix="")


@router.get("/forecast/", response_model=List[WeatherPoint], dependencies=[Security(get_firebase_admin_user)])
def get_weather_forecast(
    minutes: int = Query(60, ge=1, le=7*24*60),
    admin: dict = Depends(get_firebase_admin_user),
    measurement: str = Query(meas),
):
    """
    Get weather forecast - Firebase Admin Only

    Requires valid Firebase admin token in Authorization header:
    Authorization: Bearer <firebase_admin_token>
    """

    flux = f'''
from(bucket: "{INFLUXDB_BUCKET}")
  |> range(start: -{minutes}m)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> keep(columns: ["_time","_field","_value"])
'''

    tables = influx_query(flux)

    by_time: Dict[str, Dict[str, Any]] = {}

    for table in tables:
        for record in table.records:
            t = record.get_time().isoformat()
            field = record.get_field()
            value = record.get_value()

            if t not in by_time:
                by_time[t] = {"time": record.get_time()}
            by_time[t][field] = value

    result = list(by_time.values())
    result.sort(key=lambda x: x["time"])
    return result
