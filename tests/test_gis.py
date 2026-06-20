"""
Tests for GIS utility functions.

Exercises:
- haversine_km: known distances (same point, latitude-only, longitude-only)
- load_geojson_bytes: valid JSON decoding
- aggregate_points_to_polygons_shapely: point-in-polygon assignment, missing field, empty features
"""
import json
import math
import pytest
import pandas as pd

from gis import haversine_km, load_geojson_bytes, aggregate_points_to_polygons_shapely, HAS_SHAPELY


class TestHaversineKm:
    def test_same_point_is_zero(self):
        assert haversine_km(23.81, 90.41, 23.81, 90.41) == pytest.approx(0.0)

    def test_known_approximate_distance(self):
        # Dhaka (23.81, 90.41) → Chittagong (22.36, 91.78) ≈ 220 km
        d = haversine_km(23.81, 90.41, 22.36, 91.78)
        assert 200 < d < 250

    def test_symmetric(self):
        d1 = haversine_km(23.81, 90.41, 24.37, 88.60)
        d2 = haversine_km(24.37, 88.60, 23.81, 90.41)
        assert d1 == pytest.approx(d2)

    def test_north_pole_to_south_pole(self):
        d = haversine_km(90, 0, -90, 0)
        assert d == pytest.approx(2 * 6371 * math.pi / 2, rel=1e-3)


class TestLoadGeojsonBytes:
    def test_parses_valid_geojson(self):
        data = {"type": "FeatureCollection", "features": []}
        b = json.dumps(data).encode("utf-8")
        result = load_geojson_bytes.__wrapped__(b) if hasattr(load_geojson_bytes, "__wrapped__") else load_geojson_bytes(b)
        assert result["type"] == "FeatureCollection"
        assert result["features"] == []

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            raw = b"not valid json {"
            load_geojson_bytes.__wrapped__(raw) if hasattr(load_geojson_bytes, "__wrapped__") else load_geojson_bytes(raw)


class TestAggregatePointsToPolygons:
    """Only runs when Shapely is installed (HAS_SHAPELY=True)."""

    _SQUARE_GEOJSON = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "North"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[88, 24], [92, 24], [92, 26], [88, 26], [88, 24]]],
                },
            },
            {
                "type": "Feature",
                "properties": {"name": "South"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[88, 22], [92, 22], [92, 24], [88, 24], [88, 22]]],
                },
            },
        ],
    }

    @pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
    def test_points_assigned_to_correct_polygon(self):
        df = pd.DataFrame([
            {"city": "A", "lat": 25.0, "lon": 90.0, "temperature": 30.0},
            {"city": "B", "lat": 25.5, "lon": 90.5, "temperature": 28.0},
            {"city": "C", "lat": 23.0, "lon": 90.0, "temperature": 35.0},
        ])
        result = aggregate_points_to_polygons_shapely(df, self._SQUARE_GEOJSON, "name", "temperature")
        assert result is not None
        assert not result.empty
        north = result[result["name"] == "North"]["temperature"].values
        south = result[result["name"] == "South"]["temperature"].values
        assert len(north) == 1
        assert north[0] == pytest.approx(29.0)  # mean of 30 + 28
        assert len(south) == 1
        assert south[0] == pytest.approx(35.0)

    @pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
    def test_points_outside_all_polygons_returns_empty(self):
        df = pd.DataFrame([
            {"city": "Far", "lat": 0.0, "lon": 0.0, "temperature": 20.0},
        ])
        result = aggregate_points_to_polygons_shapely(df, self._SQUARE_GEOJSON, "name", "temperature")
        assert result is not None
        assert result.empty

    @pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
    def test_missing_polygon_id_field_skips_feature(self):
        geojson_no_field = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"other": "value"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[88, 24], [92, 24], [92, 26], [88, 26], [88, 24]]],
                    },
                }
            ],
        }
        df = pd.DataFrame([{"city": "A", "lat": 25.0, "lon": 90.0, "temperature": 30.0}])
        result = aggregate_points_to_polygons_shapely(df, geojson_no_field, "name", "temperature")
        assert result is None

    @pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
    def test_empty_features_list_returns_none(self):
        df = pd.DataFrame([{"city": "A", "lat": 25.0, "lon": 90.0, "temperature": 30.0}])
        result = aggregate_points_to_polygons_shapely(df, {"features": []}, "name", "temperature")
        assert result is None
