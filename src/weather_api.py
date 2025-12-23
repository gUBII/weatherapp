import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import streamlit as st
from weather_codes import WMO_WEATHER_CODES

def fetch_city_weather(city: str, lat: float, lon: float) -> dict | None:
    url = "https://api.open-meteo.com/v1/forecast"
    try:
        r = requests.get(
            url,
            params={"latitude": lat, "longitude": lon, "current_weather": "true", "temperature_unit": "celsius", "windspeed_unit": "ms"},
            timeout=10,
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if "current_weather" not in data:
            return None

        current_weather = data["current_weather"]
        weather_code = int(current_weather["weathercode"])
        return {
            "city": city,
            "lat": lat,
            "lon": lon,
            "temperature": float(current_weather["temperature"]),
            "feels_like": float(current_weather.get("apparent_temperature", current_weather["temperature"])), # Open-Meteo doesn't have feels_like, so use apparent_temperature or temperature
            "humidity": int(current_weather.get("relativehumidity_2m", 50)), # Placeholder if not available
            "pressure": int(current_weather.get("surface_pressure", 1013)), # Placeholder if not available
            "weather": WMO_WEATHER_CODES.get(weather_code, "Unknown"),
            "wind_speed": float(current_weather["windspeed"]),
            "clouds": int(current_weather.get("cloudcover", 50)), # Placeholder if not available
        }
    except Exception:
        return None


@st.cache_data(ttl=300)  # 5 minutes
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
