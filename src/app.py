import streamlit as st
import pandas as pd
from datetime import datetime

from config import CITIES
from weather_api import fetch_all_weather_cached, fetch_city_weather
from gis import (
    load_geojson_bytes,
    aggregate_points_to_polygons_shapely,
    haversine_km,
    HAS_SHAPELY,
)
from ui import (
    create_thermodynamic_gauges,
    create_weather_map,
    create_metric_cards_html,
    render_dashboard_header,
    apply_filters,
)
from styles import inject_styles
from streamlit_folium import st_folium

try:
    from streamlit_autorefresh import st_autorefresh
    AUTORF_AVAILABLE = True
except Exception:
    AUTORF_AVAILABLE = False


def main():
    st.set_page_config(
        page_title="Bangladesh Weather Dashboard",
        page_icon="🌦️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    # ── Sidebar: settings + GIS ───────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        auto_refresh = st.checkbox("Auto-refresh every 5 min", value=False)
        if auto_refresh:
            if AUTORF_AVAILABLE:
                st_autorefresh(interval=5 * 60 * 1000, key="weather_autorefresh")
            else:
                st.warning("Run: pip install streamlit-autorefresh")

        if st.button("🔄 Refresh Data Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 🗺️ GIS Layer")

        gis_file = st.file_uploader("Upload boundary GeoJSON", type=["geojson", "json"])
        boundary_geojson = None
        boundary_field = None
        show_boundaries = False
        show_choropleth = False
        choropleth_metric = None

        if gis_file is not None:
            try:
                boundary_geojson = load_geojson_bytes(gis_file.getvalue())
                feats = boundary_geojson.get("features", [])
                prop_keys = []
                if feats and isinstance(feats[0], dict):
                    prop_keys = list((feats[0].get("properties", {}) or {}).keys())

                if prop_keys:
                    boundary_field = st.selectbox("Polygon name/id field", prop_keys)
                else:
                    st.warning("GeoJSON features have no properties.")

                show_boundaries = st.checkbox("Show boundaries overlay", value=True)
                show_choropleth = st.checkbox("Show choropleth (polygon averages)", value=True)
                choropleth_metric = st.selectbox(
                    "Choropleth metric",
                    ["temperature", "humidity", "wind_speed", "pressure"],
                )

                if show_choropleth and not HAS_SHAPELY:
                    st.warning("Install Shapely for choropleth: pip install shapely")

            except Exception as e:
                st.error(f"Failed to read GeoJSON: {e}")

        st.markdown("---")
        st.markdown("### 🔎 Filters")

    # ── Fetch data ────────────────────────────────────────────────────────────
    cities_items = tuple(CITIES.items())
    with st.spinner("Fetching live weather data…"):
        df, fetched_at = fetch_all_weather_cached(cities_items)

    if df.empty:
        st.error("No data returned. Check your network connection.")
        return

    # ── Sidebar: dynamic filters (require df) ─────────────────────────────────
    with st.sidebar:
        selected_cities = st.multiselect(
            "Cities",
            options=sorted(df["city"].unique().tolist()),
            default=sorted(df["city"].unique().tolist()),
        )

        def _ensure_range(lo: float, hi: float, step: float) -> tuple[float, float]:
            return (lo, hi) if lo < hi else (lo, lo + step)

        tmin, tmax = _ensure_range(float(df["temperature"].min()), float(df["temperature"].max()), 0.1)
        hmin, hmax = _ensure_range(float(df["humidity"].min()), float(df["humidity"].max()), 1.0)
        wmin, wmax = _ensure_range(float(df["wind_speed"].min()), float(df["wind_speed"].max()), 0.1)

        temp_range = st.slider("Temperature (°C)", tmin, tmax, (tmin, tmax))
        humidity_range = st.slider("Humidity (%)", hmin, hmax, (hmin, hmax))
        wind_range = st.slider("Wind (m/s)", wmin, wmax, (wmin, wmax))
        condition_query = st.text_input("Condition contains", value="")

        st.markdown("---")
        st.markdown("### 🔥 Heatmap")
        heat_metric = st.selectbox("Metric", ["temperature", "humidity", "wind_speed"])

    # ── Apply filters ─────────────────────────────────────────────────────────
    # humidity_range comes back as floats from the slider; cast to int for apply_filters
    filtered = apply_filters(
        df,
        selected_cities,
        temp_range,
        (int(humidity_range[0]), int(humidity_range[1])),
        wind_range,
        condition_query,
    )

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(render_dashboard_header(len(df), len(CITIES), fetched_at), unsafe_allow_html=True)

    if filtered.empty:
        st.warning("No cities match the current filters.")
        return

    # ── KPI metric cards ──────────────────────────────────────────────────────
    st.markdown(create_metric_cards_html(filtered), unsafe_allow_html=True)

    # ── Gauges ────────────────────────────────────────────────────────────────
    st.markdown("#### 📊 Live Thermodynamic Indicators")
    st.plotly_chart(create_thermodynamic_gauges(filtered), use_container_width=True)

    # ── Map ───────────────────────────────────────────────────────────────────
    st.markdown("#### 🗺️ Interactive GIS Map")

    choropleth_df = None
    if boundary_geojson and show_choropleth and boundary_field and choropleth_metric and HAS_SHAPELY:
        choropleth_df = aggregate_points_to_polygons_shapely(
            filtered, boundary_geojson, boundary_field, choropleth_metric,
        )

    weather_map = create_weather_map(
        df=filtered,
        heat_metric=heat_metric,
        boundary_geojson=boundary_geojson,
        boundary_field=boundary_field,
        show_boundaries=show_boundaries,
        choropleth_df=choropleth_df,
        choropleth_metric=choropleth_metric,
        show_choropleth=show_choropleth,
    )
    map_state = st_folium(
        weather_map,
        width=None,
        height=560,
        returned_objects=["last_clicked", "last_active_drawing", "all_drawings"],
        use_container_width=True,
    )

    # ── GIS outputs ───────────────────────────────────────────────────────────
    with st.expander("🧭 GIS outputs — click coordinates & drawn AOI"):
        last_clicked = map_state.get("last_clicked")
        if last_clicked:
            st.write(f"**Last clicked:** lat={last_clicked.get('lat'):.5f}, lon={last_clicked.get('lng'):.5f}")
            if st.button("🌡️ Fetch weather at clicked point"):
                lat = float(last_clicked["lat"])
                lon = float(last_clicked["lng"])
                w = fetch_city_weather("Clicked Point", lat, lon)
                if w:
                    st.json(w)
                else:
                    st.warning("No data returned for clicked point.")

        last_drawn = map_state.get("last_active_drawing")
        if last_drawn:
            st.write("**Last drawn feature (GeoJSON):**")
            st.json(last_drawn)

            if HAS_SHAPELY:
                from shapely.geometry import shape, Point
                try:
                    geom = shape(last_drawn["geometry"])
                    inside = [r for _, r in filtered.iterrows() if geom.contains(Point(float(r["lon"]), float(r["lat"])))]
                    if inside:
                        inside_df = pd.DataFrame(inside)
                        st.success(f"{len(inside_df)} city/cities inside the drawn area.")
                        st.dataframe(
                            inside_df[["city", "temperature", "humidity", "wind_speed", "pressure", "weather"]],
                            use_container_width=True,
                        )
                    else:
                        c = geom.centroid
                        best, best_d = None, 1e9
                        for _, r in filtered.iterrows():
                            d = haversine_km(c.y, c.x, float(r["lat"]), float(r["lon"]))
                            if d < best_d:
                                best_d, best = d, r
                        if best is not None:
                            st.info(f"No cities inside AOI. Nearest: **{best['city']}** (~{best_d:.1f} km).")
                except Exception as e:
                    st.warning(f"Could not analyse drawn shape: {e}")
            else:
                st.warning("Install Shapely to analyse drawn AOI: pip install shapely")

    # ── Data table ────────────────────────────────────────────────────────────
    st.markdown("#### 📋 Real-Time Weather Data")
    display_df = filtered[
        ["city", "temperature", "feels_like", "humidity", "pressure", "wind_speed", "clouds", "weather"]
    ].copy()
    display_df.columns = [
        "City", "Temp (°C)", "Feels Like (°C)", "Humidity (%)",
        "Pressure (hPa)", "Wind (m/s)", "Clouds (%)", "Condition",
    ]
    st.dataframe(display_df, use_container_width=True, height=380)

    st.download_button(
        label="📥 Download filtered data as CSV",
        data=filtered.to_csv(index=False),
        file_name=f"bangladesh_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
