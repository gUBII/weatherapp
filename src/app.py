import streamlit as st
import pandas as pd
from datetime import datetime

from src.config import CITIES
from src.weather_api import fetch_all_weather_cached, fetch_city_weather
from src.gis import (
    load_geojson_bytes,
    aggregate_points_to_polygons_shapely,
    haversine_km,
    HAS_SHAPELY,
)
from src.ui import (
    create_thermodynamic_gauges,
    create_weather_map,
    apply_filters,
)
from streamlit_folium import st_folium

# Optional: auto-refresh
try:
    from streamlit_autorefresh import st_autorefresh

    AUTORF_AVAILABLE = True
except Exception:
    AUTORF_AVAILABLE = False


def main():
    st.set_page_config(
        page_title="Bangladesh Live Weather Dashboard (GIS)",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🗺️ Bangladesh Real-Time Weather Dashboard + GIS")
    st.caption(
        "Powered by Open-Meteo. Upload a GeoJSON boundary layer to overlay polygons + choropleth. Draw AOIs to summarize cities inside."
    )

    with st.sidebar:
        st.header("⚙️ Settings")

        auto_refresh = st.checkbox("🔄 Auto-refresh every 5 minutes", value=False)
        if auto_refresh:
            if AUTORF_AVAILABLE:
                st_autorefresh(interval=5 * 60 * 1000, key="weather_autorefresh")
            else:
                st.warning("Auto-refresh needs: pip install streamlit-autorefresh")

        if st.button("🔄 Refresh Data Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.subheader("🧩 GIS layer")

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
                    st.warning(
                        "GeoJSON has no properties on features (no field to join on)."
                    )

                show_boundaries = st.checkbox("Show boundaries overlay", value=True)
                show_choropleth = st.checkbox(
                    "Show choropleth (polygon averages)", value=True
                )
                choropleth_metric = st.selectbox(
                    "Choropleth metric",
                    ["temperature", "humidity", "wind_speed", "pressure"],
                    index=0,
                )

                if show_choropleth and not HAS_SHAPELY:
                    st.warning(
                        "Install Shapely to enable choropleth aggregation: pip install shapely"
                    )

            except Exception as e:
                st.error(f"Failed to read GeoJSON: {e}")

        st.markdown("---")
        st.subheader("🔎 Filters")

    cities_items = tuple(CITIES.items())
    with st.spinner("🌍 Fetching live weather data..."):
        df, fetched_at = fetch_all_weather_cached(cities_items)

    if df.empty:
        st.error("No data returned. Check network connection.")
        return

    st.success(f"✅ Loaded {len(df)} / {len(CITIES)} cities • Last fetch: {fetched_at}")

    # Filters sidebar (need ranges)
    with st.sidebar:
        selected_cities = st.multiselect(
            "Cities",
            options=sorted(df["city"].unique().tolist()),
            default=sorted(df["city"].unique().tolist()),
        )

        tmin, tmax = float(df["temperature"].min()), float(df["temperature"].max())
        hmin, hmax = int(df["humidity"].min()), int(df["humidity"].max())
        wmin, wmax = float(df["wind_speed"].min()), float(df["wind_speed"].max())

        temp_range = st.slider(
            "Temperature (°C)",
            min_value=float(tmin),
            max_value=float(tmax),
            value=(float(tmin), float(tmax)),
        )
        humidity_range = st.slider(
            "Humidity (%)",
            min_value=int(hmin),
            max_value=int(hmax),
            value=(int(hmin), int(hmax)),
        )
        wind_range = st.slider(
            "Wind (m/s)",
            min_value=float(wmin),
            max_value=float(wmax),
            value=(float(wmin), float(wmax)),
        )
        condition_query = st.text_input("Condition contains", value="")

        st.markdown("---")
        st.subheader("🔥 Heatmap")
        heat_metric = st.selectbox(
            "Heatmap metric", ["temperature", "humidity", "wind_speed"], index=0
        )

    filtered = apply_filters(
        df, selected_cities, temp_range, humidity_range, wind_range, condition_query
    )
    if filtered.empty:
        st.warning("No cities match your filters.")
        return

    # Choropleth aggregation (optional)
    choropleth_df = None
    if (
        boundary_geojson
        and show_choropleth
        and boundary_field
        and choropleth_metric
        and HAS_SHAPELY
    ):
        choropleth_df = aggregate_points_to_polygons_shapely(
            filtered,
            boundary_geojson,
            boundary_field,
            choropleth_metric,
        )

    st.subheader("📊 Live Thermodynamic Indicators (Filtered)")
    st.plotly_chart(create_thermodynamic_gauges(filtered), use_container_width=True)

    st.subheader("🗺️ GIS Map (boundaries • choropleth • draw tools • click coords)")
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

    # Only return what we need (faster)
    map_state = st_folium(
        weather_map,
        width=1400,
        height=600,
        returned_objects=["last_clicked", "last_active_drawing", "all_drawings"],
    )

    # GIS outputs panel
    with st.expander("🧭 GIS outputs (click + drawn AOI)"):
        last_clicked = map_state.get("last_clicked")
        if last_clicked:
            st.write(
                f"**Last clicked:** lat={last_clicked.get('lat')}, lon={last_clicked.get('lng')}"
            )

            # Optional: fetch weather for clicked point
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
                    inside = []
                    for _, r in filtered.iterrows():
                        p = Point(float(r["lon"]), float(r["lat"]))
                        if geom.contains(p):
                            inside.append(r)

                    if inside:
                        inside_df = pd.DataFrame(inside)
                        st.success(f"{len(inside_df)} city/cities inside the drawn area.")
                        st.dataframe(
                            inside_df[
                                [
                                    "city",
                                    "temperature",
                                    "humidity",
                                    "wind_speed",
                                    "pressure",
                                    "weather",
                                ]
                            ],
                            use_container_width=True,
                        )
                    else:
                        # fallback: nearest city to AOI centroid
                        c = geom.centroid
                        best = None
                        best_d = 1e9
                        for _, r in filtered.iterrows():
                            d = haversine_km(
                                c.y, c.x, float(r["lat"]), float(r["lon"])
                            )
                            if d < best_d:
                                best_d = d
                                best = r
                        if best is not None:
                            st.info(
                                f"No cities inside AOI. Nearest city: **{best['city']}** (~{best_d:.1f} km)."
                            )
                except Exception as e:
                    st.warning(f"Could not analyze drawn shape: {e}")
            else:
                st.warning("Install Shapely to analyze drawn AOI: pip install shapely")

    st.subheader("📋 Real-Time Weather Data (Filtered)")
    display_df = filtered[
        [
            "city",
            "temperature",
            "feels_like",
            "humidity",
            "pressure",
            "wind_speed",
            "clouds",
            "weather",
        ]
    ].copy()
    display_df.columns = [
        "City",
        "Temp (°C)",
        "Feels Like (°C)",
        "Humidity (%)",
        "Pressure (hPa)",
        "Wind (m/s)",
        "Clouds (%)",
        "Condition",
    ]
    st.dataframe(display_df, use_container_width=True, height=420)

    # Download filtered tabular data
    st.download_button(
        label="📥 Download FILTERED Weather Data (CSV)",
        data=filtered.to_csv(index=False),
        file_name=f"bangladesh_weather_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()