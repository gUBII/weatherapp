import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import streamlit as st
from weather_codes import WMO_WEATHER_CODES

# Use the modern `current=` parameter — returns real humidity, pressure, cloud cover,
# and apparent temperature, unlike the legacy `current_weather=true` which only
# provides temperature, windspeed, and weathercode.
_CURRENT_VARS = (
    "temperature_2m,"
    "relative_humidity_2m,"
    "apparent_temperature,"
    "surface_pressure,"
    "cloud_cover,"
    "wind_speed_10m,"
    "weather_code"
)


def fetch_city_weather(city: str, lat: float, lon: float) -> dict | None:
    url = "https://api.open-meteo.com/v1/forecast"
    try:
        r = requests.get(
            url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": _CURRENT_VARS,
                "temperature_unit": "celsius",
                "windspeed_unit": "ms",
            },
            timeout=10,
        )
        if r.status_code != 200:
            return None

        data = r.json()
        current = data.get("current")
        if not current:
            return None

        weather_code = int(current.get("weather_code", 0))
        temp = float(current.get("temperature_2m", 0.0))
        return {
            "city": city,
            "lat": lat,
            "lon": lon,
            "temperature": temp,
            "feels_like": float(current.get("apparent_temperature", temp)),
            "humidity": int(current.get("relative_humidity_2m", 0)),
            "pressure": float(current.get("surface_pressure", 1013.0)),
            "weather": WMO_WEATHER_CODES.get(weather_code, "Unknown"),
            "wind_speed": float(current.get("wind_speed_10m", 0.0)),
            "clouds": int(current.get("cloud_cover", 0)),
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def fetch_all_weather_cached(cities_items: tuple) -> tuple[pd.DataFrame, str]:
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(12, max(4, len(cities_items)))) as ex:
        futures = [ex.submit(fetch_city_weather, c, ll[0], ll[1]) for c, ll in cities_items]
        for f in as_completed(futures):
            res = f.result()
            if res:
                rows.append(res)

    df = pd.DataFrame(rows)
    fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df, fetched_at
