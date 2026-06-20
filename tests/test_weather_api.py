"""
Tests for weather_api.fetch_city_weather.

Exercises:
- Happy path: 200 response with full current fields
- Non-200 response → None
- Missing 'current' key in response body → None
- Network exception → None
- Missing optional fields fall back to sensible defaults
"""
import json
import pytest
from unittest.mock import patch, MagicMock

import weather_api
from weather_api import fetch_city_weather


def _make_response(status: int, payload: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload
    return r


_FULL_CURRENT = {
    "temperature_2m": 30.5,
    "apparent_temperature": 34.2,
    "relative_humidity_2m": 78,
    "surface_pressure": 1005.0,
    "cloud_cover": 40,
    "wind_speed_10m": 3.5,
    "weather_code": 2,
}


class TestFetchCityWeather:
    def test_happy_path_returns_correct_fields(self):
        payload = {"current": _FULL_CURRENT}
        with patch("weather_api.requests.get", return_value=_make_response(200, payload)):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)

        assert result is not None
        assert result["city"] == "Dhaka"
        assert result["temperature"] == pytest.approx(30.5)
        assert result["feels_like"] == pytest.approx(34.2)
        assert result["humidity"] == 78
        assert result["pressure"] == pytest.approx(1005.0)
        assert result["clouds"] == 40
        assert result["wind_speed"] == pytest.approx(3.5)
        assert result["weather"] == "Partly cloudy"
        assert result["lat"] == pytest.approx(23.81)
        assert result["lon"] == pytest.approx(90.41)

    def test_non_200_returns_none(self):
        with patch("weather_api.requests.get", return_value=_make_response(503, {})):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)
        assert result is None

    def test_missing_current_key_returns_none(self):
        payload = {"hourly": {}}
        with patch("weather_api.requests.get", return_value=_make_response(200, payload)):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)
        assert result is None

    def test_empty_current_dict_returns_none(self):
        payload = {"current": None}
        with patch("weather_api.requests.get", return_value=_make_response(200, payload)):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)
        assert result is None

    def test_network_exception_returns_none(self):
        with patch("weather_api.requests.get", side_effect=ConnectionError("timeout")):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)
        assert result is None

    def test_unknown_weather_code_returns_unknown(self):
        payload = {"current": {**_FULL_CURRENT, "weather_code": 999}}
        with patch("weather_api.requests.get", return_value=_make_response(200, payload)):
            result = fetch_city_weather("Dhaka", 23.81, 90.41)
        assert result is not None
        assert result["weather"] == "Unknown"

    def test_missing_optional_fields_fall_back(self):
        minimal = {"temperature_2m": 25.0, "weather_code": 0}
        with patch("weather_api.requests.get", return_value=_make_response(200, {"current": minimal})):
            result = fetch_city_weather("TestCity", 0.0, 0.0)

        assert result is not None
        assert result["temperature"] == pytest.approx(25.0)
        assert result["feels_like"] == pytest.approx(25.0)  # falls back to temp
        assert result["humidity"] == 0
        assert result["pressure"] == pytest.approx(1013.0)
        assert result["clouds"] == 0
        assert result["wind_speed"] == pytest.approx(0.0)

    def test_request_uses_timeout(self):
        with patch("weather_api.requests.get", return_value=_make_response(200, {"current": _FULL_CURRENT})) as mock_get:
            fetch_city_weather("Dhaka", 23.81, 90.41)
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs.get("timeout") is not None or (
            len(call_kwargs.args) >= 2 and "timeout" in str(call_kwargs)
        )
