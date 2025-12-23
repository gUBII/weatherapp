import json
import math
import pandas as pd
import streamlit as st

# Optional: GIS analytics (AOI / choropleth aggregation)
try:
    from shapely.geometry import shape, Point
    HAS_SHAPELY = True
except Exception:
    HAS_SHAPELY = False


@st.cache_data
def load_geojson_bytes(b: bytes) -> dict:
    # Works for typical UTF-8 GeoJSON uploads
    return json.loads(b.decode("utf-8"))


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    # Earth radius
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def aggregate_points_to_polygons_shapely(
    points_df: pd.DataFrame,
    boundary_geojson: dict,
    polygon_id_field: str,
    metric: str,
) -> pd.DataFrame | None:
    """
    Assign each point to the first polygon that contains it and compute mean(metric) per polygon.
    Requires shapely.
    """
    if not HAS_SHAPELY:
        return None

    feats = boundary_geojson.get("features", [])
    if not feats:
        return None

    polygons = []
    for feat in feats:
        props = feat.get("properties", {}) or {}
        if polygon_id_field not in props:
            continue
        try:
            geom = shape(feat["geometry"])
        except Exception:
            continue
        polygons.append((props[polygon_id_field], geom))

    if not polygons:
        return None

    poly_ids = []
    for _, r in points_df.iterrows():
        p = Point(float(r["lon"]), float(r["lat"]))  # GeoJSON order is lon,lat
        hit = None
        for pid, geom in polygons:
            if geom.contains(p):
                hit = pid
                break
        poly_ids.append(hit)

    temp = points_df.copy()
    temp["_poly_id"] = poly_ids
    temp = temp.dropna(subset=["_poly_id"])
    if temp.empty:
        return pd.DataFrame(columns=[polygon_id_field, metric])

    agg = temp.groupby("_poly_id")[metric].mean().reset_index()
    agg.columns = [polygon_id_field, metric]
    return agg
