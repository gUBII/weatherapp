import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap, Draw, MeasureControl
from streamlit_folium import st_folium

def create_thermodynamic_gauges(df: pd.DataFrame) -> go.Figure:
    avg_temp = float(df["temperature"].mean())
    avg_humidity = float(df["humidity"].mean())
    avg_pressure = float(df["pressure"].mean())

    fig = make_subplots(
        rows=1,
        cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=("Live Temperature", "Live Humidity", "Live Pressure"),
    )

    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=avg_temp,
            title={"text": "°C", "font": {"size": 20}},
            delta={"reference": 25},
            gauge={
                "axis": {"range": [0, 45]},
                "steps": [
                    {"range": [0, 15], "color": "lightblue"},
                    {"range": [15, 25], "color": "lightgreen"},
                    {"range": [25, 35], "color": "yellow"},
                    {"range": [35, 45], "color": "red"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "value": 35},
            },
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=avg_humidity,
            title={"text": "%", "font": {"size": 20}},
            gauge={"axis": {"range": [0, 100]}},
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=avg_pressure,
            title={"text": "hPa", "font": {"size": 20}},
            gauge={"axis": {"range": [980, 1040]}},
        ),
        row=1,
        col=3,
    )

    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_weather_map(
    df: pd.DataFrame,
    heat_metric: str,
    boundary_geojson: dict | None,
    boundary_field: str | None,
    show_boundaries: bool,
    choropleth_df: pd.DataFrame | None,
    choropleth_metric: str | None,
    show_choropleth: bool,
) -> folium.Map:
    m = folium.Map(
        location=[23.685, 90.3563],
        zoom_start=7,
        tiles=None,
        control_scale=True,
    )

    # Base layers (GIS-ish)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("CartoDB positron", name="Positron").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Imagery",
    ).add_to(m)

    # GIS tools
    Draw(export=False).add_to(m)  # draw polygon/rectangle
    MeasureControl(primary_length_unit="kilometers").add_to(m)
    folium.LatLngPopup().add_to(m)

    # Optional: boundaries overlay
    if boundary_geojson and show_boundaries:
        tooltip = None
        if boundary_field:
            tooltip = folium.GeoJsonTooltip(fields=[boundary_field], aliases=["Area:"])
        folium.GeoJson(
            boundary_geojson,
            name="Boundaries",
            tooltip=tooltip,
            style_function=lambda _: {"weight": 1, "opacity": 0.7},
        ).add_to(m)

    # Optional: choropleth layer
    if (
        boundary_geojson
        and show_choropleth
        and choropleth_df is not None
        and choropleth_metric
        and boundary_field
        and not choropleth_df.empty
    ):
        folium.Choropleth(
            geo_data=boundary_geojson,
            name=f"{choropleth_metric} choropleth",
            data=choropleth_df,
            columns=[boundary_field, choropleth_metric],
            key_on=f"feature.properties.{boundary_field}",
            fill_opacity=0.6,
            line_opacity=0.2,
        ).add_to(m)

    # City markers + heatmap
    heat_data = []
    for _, row in df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 240px; background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <h3 style="margin: 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">{row['city']}</h3>
            <div style="margin-top: 10px;">
                <p style="margin: 5px 0;"><b>🌡️ Temperature:</b> {row['temperature']:.1f}°C</p>
                <p style="margin: 5px 0;"><b>🤚 Feels Like:</b> {row['feels_like']:.1f}°C</p>
                <p style="margin: 5px 0;"><b>💧 Humidity:</b> {row['humidity']}%</p>
                <p style="margin: 5px 0;"><b>💨 Wind Speed:</b> {row['wind_speed']:.1f} m/s</p>
                <p style="margin: 5px 0;"><b>🔽 Pressure:</b> {row['pressure']} hPa</p>
                <p style="margin: 5px 0;"><b>☁️ Cloud Cover:</b> {row['clouds']}%</p>
                <p style="margin: 5px 0;"><b>📋 Condition:</b> {str(row['weather']).title()}</p>
            </div>
        </div>
        """

        temp = float(row["temperature"])
        color = "blue" if temp < 20 else ("green" if temp < 30 else "red")

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"<b>{row['city']}</b><br>{temp:.1f}°C - {str(row['weather']).title()}",
            icon=folium.Icon(color=color, icon="cloud", prefix="fa"),
        ).add_to(m)

        heat_val = float(row[heat_metric])
        heat_data.append([row["lat"], row["lon"], heat_val])

    HeatMap(
        heat_data,
        name=f"{heat_metric} heatmap",
        min_opacity=0.35,
        radius=25,
        blur=15,
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def apply_filters(df: pd.DataFrame,
                  selected_cities: list[str],
                  temp_range: tuple[float, float],
                  humidity_range: tuple[int, int],
                  wind_range: tuple[float, float],
                  condition_query: str) -> pd.DataFrame:
    out = df.copy()

    if selected_cities:
        out = out[out["city"].isin(selected_cities)]

    out = out[
        (out["temperature"].between(temp_range[0], temp_range[1]))
        & (out["humidity"].between(humidity_range[0], humidity_range[1]))
        & (out["wind_speed"].between(wind_range[0], wind_range[1]))
    ]

    q = (condition_query or "").strip().lower()
    if q:
        out = out[out["weather"].astype(str).str.lower().str.contains(q, na=False)]

    return out.reset_index(drop=True)
