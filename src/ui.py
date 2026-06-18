import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap, Draw, MeasureControl


# ── Colour helpers ────────────────────────────────────────────────────────────

def _temp_accent(temp: float) -> str:
    if temp < 20:
        return "#3b82f6"   # blue
    elif temp < 28:
        return "#22c55e"   # green
    elif temp < 33:
        return "#f59e0b"   # amber
    return "#ef4444"       # red


def _humidity_accent(rh: float) -> str:
    if rh < 40:
        return "#f59e0b"
    elif rh < 70:
        return "#06b6d4"
    return "#3b82f6"


# ── Metric cards (HTML) ───────────────────────────────────────────────────────

def _card(label: str, value: str, unit: str, sub: str, accent: str, icon: str) -> str:
    return f"""
    <div style="
        background: #111827;
        border: 1px solid #1e2d3d;
        border-top: 2px solid {accent};
        border-radius: 10px;
        padding: 16px 18px;
        position: relative;
    ">
        <div style="
            position: absolute; top: 14px; right: 14px;
            font-size: 18px; opacity: 0.5;
        ">{icon}</div>
        <div style="
            font-size: 10.5px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.09em;
            color: #475569; margin-bottom: 8px;
            font-family: -apple-system, 'Inter', sans-serif;
        ">{label}</div>
        <div style="
            font-size: 26px; font-weight: 700; line-height: 1;
            color: #e2e8f0;
            font-family: -apple-system, 'Inter', sans-serif;
        ">{value}<span style="font-size: 14px; color: #64748b; font-weight: 400; margin-left: 3px;">{unit}</span></div>
        <div style="
            font-size: 11px; color: #475569; margin-top: 7px;
            font-family: -apple-system, 'Inter', sans-serif;
        ">{sub}</div>
    </div>"""


def create_metric_cards_html(df: pd.DataFrame) -> str:
    """Return an HTML block with four KPI metric cards for the filtered dataset."""
    n = len(df)
    if n == 0:
        return ""

    avg_temp = df["temperature"].mean()
    avg_hum = df["humidity"].mean()
    avg_wind = df["wind_speed"].mean()
    max_temp = df["temperature"].max()
    min_temp = df["temperature"].min()

    temp_accent = _temp_accent(avg_temp)
    hum_accent = _humidity_accent(avg_hum)

    cards_html = "".join([
        _card(
            "Avg Temperature",
            f"{avg_temp:.1f}", "°C",
            f"Range: {min_temp:.1f}°–{max_temp:.1f}°C",
            temp_accent, "🌡️",
        ),
        _card(
            "Avg Humidity",
            f"{avg_hum:.0f}", "%",
            f"Max: {df['humidity'].max():.0f}% · Min: {df['humidity'].min():.0f}%",
            hum_accent, "💧",
        ),
        _card(
            "Avg Wind Speed",
            f"{avg_wind:.1f}", "m/s",
            f"Gusts up to {df['wind_speed'].max():.1f} m/s",
            "#8b5cf6", "💨",
        ),
        _card(
            "Cities Tracked",
            str(n), "",
            f"Avg pressure: {df['pressure'].mean():.0f} hPa",
            "#22c55e", "📍",
        ),
    ])

    return f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 4px 0 20px 0;">
        {cards_html}
    </div>"""


# ── Dashboard header (HTML) ───────────────────────────────────────────────────

def render_dashboard_header(n_loaded: int, n_total: int, fetched_at: str) -> str:
    return f"""
    <div style="
        background: linear-gradient(135deg, #0d1117 0%, #111827 60%, #0f172a 100%);
        border: 1px solid #1e2d3d;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <div>
            <div style="
                font-size: 20px; font-weight: 700; color: #e2e8f0;
                letter-spacing: -0.03em; margin: 0;
                font-family: -apple-system, 'Inter', sans-serif;
            ">🌦️ Bangladesh Weather Dashboard</div>
            <div style="
                font-size: 12.5px; color: #64748b; margin-top: 4px;
                font-family: -apple-system, 'Inter', sans-serif;
            ">Real-time data across 10 cities · Open-Meteo API · Updated {fetched_at}</div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="
                display: inline-flex; align-items: center; gap: 6px;
                background: rgba(34, 197, 94, 0.08);
                border: 1px solid rgba(34, 197, 94, 0.22);
                border-radius: 100px; padding: 5px 12px;
                font-size: 11.5px; font-weight: 500; color: #22c55e;
                font-family: -apple-system, 'Inter', sans-serif;
            ">
                <span style="
                    width: 6px; height: 6px; border-radius: 50%;
                    background: #22c55e; display: inline-block;
                "></span>
                {n_loaded}/{n_total} Live
            </div>
        </div>
    </div>"""


# ── Thermodynamic gauges (Plotly, dark theme) ─────────────────────────────────

def create_thermodynamic_gauges(df: pd.DataFrame) -> go.Figure:
    avg_temp = float(df["temperature"].mean())
    avg_hum = float(df["humidity"].mean())
    avg_pres = float(df["pressure"].mean())

    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=("Avg Temperature", "Avg Humidity", "Avg Pressure"),
    )

    # Temperature
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=avg_temp,
        number={"suffix": "°C", "font": {"size": 26, "color": "#e2e8f0"}},
        delta={"reference": 27, "valueformat": ".1f", "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 45], "tickcolor": "#334155", "tickfont": {"size": 10, "color": "#475569"}},
            "bar": {"color": _temp_accent(avg_temp)},
            "bgcolor": "#1e293b",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 15], "color": "#0c1526"},
                {"range": [15, 27], "color": "#0c2236"},
                {"range": [27, 35], "color": "#1a2a0c"},
                {"range": [35, 45], "color": "#2a100c"},
            ],
            "threshold": {"line": {"color": "#ef4444", "width": 2}, "value": 36},
        },
    ), row=1, col=1)

    # Humidity
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=avg_hum,
        number={"suffix": "%", "font": {"size": 26, "color": "#e2e8f0"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#334155", "tickfont": {"size": 10, "color": "#475569"}},
            "bar": {"color": _humidity_accent(avg_hum)},
            "bgcolor": "#1e293b",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "#0c1526"},
                {"range": [30, 60], "color": "#0c2236"},
                {"range": [60, 80], "color": "#062030"},
                {"range": [80, 100], "color": "#061a30"},
            ],
        },
    ), row=1, col=2)

    # Pressure
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=avg_pres,
        number={"suffix": " hPa", "font": {"size": 22, "color": "#e2e8f0"}},
        gauge={
            "axis": {"range": [980, 1040], "tickcolor": "#334155", "tickfont": {"size": 10, "color": "#475569"}},
            "bar": {"color": "#8b5cf6"},
            "bgcolor": "#1e293b",
            "borderwidth": 0,
            "steps": [
                {"range": [980, 1000], "color": "#1a0c2a"},
                {"range": [1000, 1020], "color": "#0c1526"},
                {"range": [1020, 1040], "color": "#0c1a2a"},
            ],
        },
    ), row=1, col=3)

    fig.update_layout(
        height=280,
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0a0f1e",
        font={"family": "Inter, -apple-system, sans-serif", "color": "#e2e8f0"},
        margin=dict(l=30, r=30, t=48, b=10),
    )
    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color="#94a3b8", family="Inter, -apple-system, sans-serif")

    return fig


# ── Weather map (Folium, dark tile default) ───────────────────────────────────

def _marker_icon_html(temp: float) -> str:
    color = _temp_accent(temp)
    return f"""
    <div style="
        background: {color};
        color: #fff;
        border-radius: 50%;
        width: 36px; height: 36px;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700;
        border: 2px solid rgba(255,255,255,0.2);
        box-shadow: 0 2px 8px rgba(0,0,0,0.55), 0 0 0 3px {color}30;
        font-family: -apple-system, sans-serif;
        letter-spacing: -0.5px;
    ">{round(temp)}°</div>"""


def _popup_html(row: pd.Series) -> str:
    return f"""
    <div style="
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background: rgba(15, 23, 42, 0.97);
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 14px 16px;
        min-width: 210px;
        color: #e2e8f0;
        box-shadow: 0 8px 28px rgba(0,0,0,0.6);
    ">
        <div style="
            font-size: 14px; font-weight: 600; color: #60a5fa;
            border-bottom: 1px solid #1e3a5f;
            padding-bottom: 8px; margin-bottom: 10px;
        ">{row['city']}</div>
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <tr>
                <td style="color:#64748b; padding:3px 0;">🌡️ Temperature</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['temperature']:.1f}°C</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">🌡️ Feels Like</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['feels_like']:.1f}°C</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">💧 Humidity</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['humidity']}%</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">💨 Wind</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['wind_speed']:.1f} m/s</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">⬇️ Pressure</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['pressure']:.0f} hPa</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">☁️ Cloud Cover</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{row['clouds']}%</td>
            </tr>
            <tr>
                <td style="color:#64748b; padding:3px 0;">📋 Condition</td>
                <td style="color:#e2e8f0; font-weight:500; text-align:right;">{str(row['weather']).title()}</td>
            </tr>
        </table>
    </div>"""


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
    # Dark tile as default for visual consistency with the dashboard theme
    m = folium.Map(
        location=[23.685, 90.3563],
        zoom_start=7,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Alternative tile layers
    folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
    folium.TileLayer("CartoDB positron", name="Light").add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
    ).add_to(m)

    Draw(export=False).add_to(m)
    MeasureControl(primary_length_unit="kilometers").add_to(m)
    folium.LatLngPopup().add_to(m)

    if boundary_geojson and show_boundaries:
        tooltip = None
        if boundary_field:
            tooltip = folium.GeoJsonTooltip(fields=[boundary_field], aliases=["Area:"])
        folium.GeoJson(
            boundary_geojson,
            name="Boundaries",
            tooltip=tooltip,
            style_function=lambda _: {"weight": 1.5, "color": "#3b82f6", "fillOpacity": 0.05},
        ).add_to(m)

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
            fill_opacity=0.55,
            line_opacity=0.2,
        ).add_to(m)

    heat_data = []
    for _, row in df.iterrows():
        temp = float(row["temperature"])

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(_popup_html(row), max_width=260),
            tooltip=f"<b style='font-family:-apple-system,sans-serif;'>{row['city']}</b>"
                    f"<br><span style='color:#94a3b8;'>{temp:.1f}°C · {str(row['weather']).title()}</span>",
            icon=folium.DivIcon(
                html=_marker_icon_html(temp),
                icon_size=(36, 36),
                icon_anchor=(18, 18),
            ),
        ).add_to(m)

        heat_val = float(row[heat_metric])
        heat_data.append([row["lat"], row["lon"], heat_val])

    HeatMap(
        heat_data,
        name=f"{heat_metric} heatmap",
        min_opacity=0.3,
        radius=28,
        blur=18,
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ── Filter helper ─────────────────────────────────────────────────────────────

def apply_filters(
    df: pd.DataFrame,
    selected_cities: list[str],
    temp_range: tuple[float, float],
    humidity_range: tuple[int, int],
    wind_range: tuple[float, float],
    condition_query: str,
) -> pd.DataFrame:
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
