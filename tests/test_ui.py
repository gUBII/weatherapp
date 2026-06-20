"""
Tests for UI helpers in ui.py.

Exercises:
- apply_filters: city multiselect, temperature/humidity/wind sliders, condition text search
- _temp_accent / _humidity_accent: correct colour returned per band
- create_metric_cards_html: empty DataFrame → empty string; normal DataFrame → contains expected values
"""
import pytest
import pandas as pd

from ui import apply_filters, create_metric_cards_html, _temp_accent, _humidity_accent


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"city": "Dhaka",      "temperature": 32.0, "feels_like": 36.0, "humidity": 80, "wind_speed": 3.0, "pressure": 1005.0, "clouds": 60, "weather": "Partly cloudy"},
        {"city": "Chittagong", "temperature": 28.0, "feels_like": 31.0, "humidity": 70, "wind_speed": 5.0, "pressure": 1010.0, "clouds": 40, "weather": "Clear sky"},
        {"city": "Khulna",     "temperature": 35.0, "feels_like": 40.0, "humidity": 90, "wind_speed": 2.0, "pressure": 1000.0, "clouds": 80, "weather": "Moderate rain"},
    ])


class TestApplyFilters:
    def test_city_filter_keeps_selected(self, sample_df):
        out = apply_filters(sample_df, ["Dhaka"], (20.0, 40.0), (0, 100), (0.0, 20.0), "")
        assert list(out["city"]) == ["Dhaka"]

    def test_city_filter_empty_list_returns_all(self, sample_df):
        # empty list = no city filter applied (all cities pass through)
        out = apply_filters(sample_df, [], (20.0, 40.0), (0, 100), (0.0, 20.0), "")
        assert len(out) == 3

    def test_all_cities_when_all_selected(self, sample_df):
        cities = sample_df["city"].tolist()
        out = apply_filters(sample_df, cities, (20.0, 40.0), (0, 100), (0.0, 20.0), "")
        assert len(out) == 3

    def test_temperature_range_filters(self, sample_df):
        # Only Chittagong (28°) should survive 27-30 range
        out = apply_filters(sample_df, sample_df["city"].tolist(), (27.0, 30.0), (0, 100), (0.0, 20.0), "")
        assert list(out["city"]) == ["Chittagong"]

    def test_humidity_range_filters(self, sample_df):
        # Only Chittagong (70%) inside 60-75
        out = apply_filters(sample_df, sample_df["city"].tolist(), (20.0, 40.0), (60, 75), (0.0, 20.0), "")
        assert list(out["city"]) == ["Chittagong"]

    def test_wind_range_filters(self, sample_df):
        # Khulna (2.0 m/s) and Dhaka (3.0) inside 1-4
        out = apply_filters(sample_df, sample_df["city"].tolist(), (20.0, 40.0), (0, 100), (1.0, 4.0), "")
        assert set(out["city"]) == {"Dhaka", "Khulna"}

    def test_condition_query_case_insensitive(self, sample_df):
        out = apply_filters(sample_df, sample_df["city"].tolist(), (20.0, 40.0), (0, 100), (0.0, 20.0), "RAIN")
        assert list(out["city"]) == ["Khulna"]

    def test_condition_query_empty_string_returns_all(self, sample_df):
        out = apply_filters(sample_df, sample_df["city"].tolist(), (20.0, 40.0), (0, 100), (0.0, 20.0), "")
        assert len(out) == 3

    def test_condition_query_no_match_returns_empty(self, sample_df):
        out = apply_filters(sample_df, sample_df["city"].tolist(), (20.0, 40.0), (0, 100), (0.0, 20.0), "snow")
        assert out.empty

    def test_output_resets_index(self, sample_df):
        out = apply_filters(sample_df, ["Khulna"], (20.0, 40.0), (0, 100), (0.0, 20.0), "")
        assert list(out.index) == [0]


class TestTempAccent:
    def test_cold_is_blue(self):
        assert _temp_accent(15.0) == "#3b82f6"

    def test_comfortable_is_green(self):
        assert _temp_accent(25.0) == "#22c55e"

    def test_warm_is_amber(self):
        assert _temp_accent(30.0) == "#f59e0b"

    def test_hot_is_red(self):
        assert _temp_accent(34.0) == "#ef4444"

    def test_boundary_exactly_20_is_green(self):
        assert _temp_accent(20.0) == "#22c55e"

    def test_boundary_exactly_28_is_amber(self):
        assert _temp_accent(28.0) == "#f59e0b"

    def test_boundary_exactly_33_is_red(self):
        assert _temp_accent(33.0) == "#ef4444"


class TestHumidityAccent:
    def test_dry_is_amber(self):
        assert _humidity_accent(30.0) == "#f59e0b"

    def test_moderate_is_cyan(self):
        assert _humidity_accent(55.0) == "#06b6d4"

    def test_humid_is_blue(self):
        assert _humidity_accent(80.0) == "#3b82f6"

    def test_boundary_exactly_40_is_cyan(self):
        assert _humidity_accent(40.0) == "#06b6d4"

    def test_boundary_exactly_70_is_blue(self):
        assert _humidity_accent(70.0) == "#3b82f6"


class TestCreateMetricCardsHtml:
    def test_empty_df_returns_empty_string(self):
        empty = pd.DataFrame(columns=["temperature", "humidity", "wind_speed", "pressure"])
        result = create_metric_cards_html(empty)
        assert result == ""

    def test_normal_df_contains_avg_temperature(self, sample_df):
        html = create_metric_cards_html(sample_df)
        avg = (32.0 + 28.0 + 35.0) / 3
        assert f"{avg:.1f}" in html

    def test_normal_df_contains_city_count(self, sample_df):
        html = create_metric_cards_html(sample_df)
        assert ">3<" in html or ">3 " in html or "3<" in html
