"""
Tests for the WMO weather code mapping.
"""
import pytest
from weather_codes import WMO_WEATHER_CODES


class TestWmoWeatherCodes:
    def test_clear_sky_is_code_0(self):
        assert WMO_WEATHER_CODES[0] == "Clear sky"

    def test_thunderstorm_is_code_95(self):
        assert WMO_WEATHER_CODES[95] == "Thunderstorm"

    def test_all_values_are_non_empty_strings(self):
        for code, description in WMO_WEATHER_CODES.items():
            assert isinstance(description, str), f"code {code} is not a string"
            assert description.strip(), f"code {code} has empty description"

    def test_missing_code_returns_none(self):
        assert WMO_WEATHER_CODES.get(999) is None
