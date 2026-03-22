"""Streamlit dashboard for France ENTSO-E energy data."""

import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from entsoe_ai_warriors.collect_france import main as collect_data
from entsoe_ai_warriors.process_france import main as process_data
from entsoe_ai_warriors.process_france import (
    COL_ACTUAL_LOAD,
    COL_EXPORT,
    COL_FORECAST_LOAD,
    COL_IMPORT,
    COL_NET_IMPORT,
    COL_PRICE,
    PROCESSED_DIR,
)

# ── Adalan-inspired Theme ─────────────────────────────────────────────────────
# Palette: corporate blue #2299DD, orange accent #F57C00, clean white/navy tones

ADALAN_COLORS = [
    "#2299DD",  # Adalan Blue
    "#F57C00",  # Orange accent
    "#00ACC1",  # Teal
    "#43A047",  # Green
    "#8E24AA",  # Purple
    "#E53935",  # Red
    "#FB8C00",  # Amber
    "#3949AB",  # Indigo
]

ADALAN_FONT = "'Inter', 'Segoe UI', Arial, sans-serif"

ADALAN_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        font=dict(family=ADALAN_FONT, color="#1A2940"),
        title=dict(font=dict(size=17, color="#1A2940")),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F4F7FB",
        colorway=ADALAN_COLORS,
        xaxis=dict(
            gridcolor="rgba(34,153,221,0.12)",
            linecolor="#CBD5E1",
            zerolinecolor="rgba(26,41,64,0.15)",
        ),
        yaxis=dict(
            gridcolor="rgba(34,153,221,0.12)",
            linecolor="#CBD5E1",
            zerolinecolor="rgba(26,41,64,0.15)",
        ),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#CBD5E1", borderwidth=1),
    ),
    data=dict(
        scatter=[go.Scatter(line=dict(width=2.5))],
        bar=[go.Bar(marker=dict(line=dict(width=0, color="#FFFFFF")))],
        pie=[go.Pie(marker=dict(line=dict(width=1, color="#FFFFFF")))],
    ),
)

SOURCE_COLORS = {
    "Solar": "#F57C00",                          # Orange
    "Hydro Pumped Storage": "#2299DD",            # Adalan Blue
    "Hydro Run-of-river and poundage": "#00ACC1", # Teal
    "Hydro Water Reservoir": "#3949AB",           # Indigo
}

pio.templates["adalan"] = ADALAN_TEMPLATE
pio.templates.default = "adalan"

# ── Constants ────────────────────────────────────────────────────────────────

REFRESH_INTERVAL_SECONDS = 15 * 60  # 15 minutes

# Energy conversion: 15-min interval MW readings to GWh
INTERVAL_HOURS = 0.25  # 15 minutes expressed in hours
MW_TO_GWH = INTERVAL_HOURS / 1000  # multiply sum of MW values by this to get GWh

logger = logging.getLogger(__name__)

# Shared state for the background thread (module-level, survives Streamlit reruns)
_refresh_lock = threading.Lock()
_refresh_in_progress = False
_refresh_last_error: str | None = None
_last_data_update: float = 0.0  # timestamp of last successful data refresh

POLL_INTERVAL_SECONDS = 30  # how often each Streamlit session checks for new data

NEIGHBOURS = ["BE", "CH", "DE_LU", "ES", "GB", "IT_NORD"]
NEIGHBOUR_LABELS = {
    "BE": "Belgium",
    "CH": "Switzerland",
    "DE_LU": "Germany/Lux",
    "ES": "Spain",
    "GB": "Great Britain",
    "IT_NORD": "Italy North",
}

RENEWABLE_TYPES = {"Solar", "Wind Offshore", "Wind Onshore", "Hydro Run-of-river and poundage", "Hydro Water Reservoir"}
NUCLEAR_TYPES = {"Nuclear"}


def _refresh_loop() -> None:
    """Background loop: collect and process fresh data every 15 minutes."""
    global _refresh_in_progress, _refresh_last_error, _last_data_update
    while True:
        try:
            with _refresh_lock:
                _refresh_in_progress = True
                _refresh_last_error = None
            logger.info("Starting data refresh from ENTSO-E API...")
            collect_data()
            process_data()
            with _refresh_lock:
                _refresh_in_progress = False
                _last_data_update = time.time()
            st.cache_data.clear()
            logger.info("Data refresh completed")
        except Exception as exc:
            with _refresh_lock:
                _refresh_in_progress = False
                _refresh_last_error = str(exc)
            logger.exception("Data refresh failed")
        time.sleep(REFRESH_INTERVAL_SECONDS)


def _ensure_refresh_thread() -> None:
    """Start the background refresh thread once per process."""
    if "refresh_thread_started" not in st.session_state:
        thread = threading.Thread(target=_refresh_loop, daemon=True)
        thread.start()
        st.session_state.refresh_thread_started = True


def _safe_pct(numerator: float, denominator: float) -> float:
    """Compute percentage safely, returning 0 if denominator is zero or NaN."""
    if pd.notna(denominator) and denominator > 0:
        return numerator / denominator * 100
    return 0.0


def _to_gwh(mw_sum: float) -> float:
    """Convert a sum of MW values (from 15-min interval data) to GWh."""
    return mw_sum * MW_TO_GWH


# ── Data loading ────────────────────────────────────────────────────────────


@st.cache_data
def load_prices() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "prices.csv", index_col=0, parse_dates=True)
    if df.empty:
        raise ValueError("Price data is empty")
    return df


@st.cache_data
def load_load() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "load.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_generation() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "generation.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_wind_solar_forecast() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "wind_solar_forecast.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_installed_capacity() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "installed_capacity.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_crossborder() -> dict[str, pd.DataFrame]:
    flows: dict[str, pd.DataFrame] = {}
    for nb in NEIGHBOURS:
        flows[nb] = pd.read_csv(
            PROCESSED_DIR / f"crossborder_{nb}.csv", index_col=0, parse_dates=True
        )
    return flows


# ── Helpers ─────────────────────────────────────────────────────────────────


def filter_by_date(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    mask = (df.index >= start) & (df.index < end)
    return df.loc[mask]


# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="France Energy Dashboard", page_icon="⚡", layout="wide")

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

_text        = "#1A2940"
_metric_val  = "#2299DD"
_hline_color = "#1A2940"

st.markdown("""
<style>
    .stApp {
        background-color: #F4F7FB;
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1A3A5C;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h4,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        color: #FFFFFF !important;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp [data-testid="stHeading"] h1,
    .stApp [data-testid="stHeading"] h2,
    .stApp [data-testid="stHeading"] h3,
    .stApp [data-testid="stHeading"] h4,
    .stApp .stMarkdown h1, .stApp .stMarkdown h2,
    .stApp .stMarkdown h3, .stApp .stMarkdown h4 {
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600;
        color: #1A2940;
    }
    .stApp p, .stApp span, .stApp label, .stApp .stCaption {
        font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        color: #1A2940;
    }
    [data-testid="stMetricValue"] {
        color: #2299DD;
        font-weight: 600;
    }
    [data-testid="stMetricLabel"] {
        color: #1A2940;
    }
    /* Remove white frame around Plotly charts */
    .stPlotlyChart, [data-testid="stPlotlyChart"],
    .stPlotlyChart > div, [data-testid="stPlotlyChart"] > div,
    .stPlotlyChart iframe, [data-testid="stPlotlyChart"] iframe {
        background-color: transparent !important;
    }
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<h1 style="font-family: \'Inter\', \'Segoe UI\', Arial, sans-serif; font-weight: 700; color: #1A2940;">⚡ France Energy Dashboard — ENTSO-E Data</h1>',
    unsafe_allow_html=True,
)

# ── Initial data collection if processed CSVs are missing ──────────────────

_required_csv = PROCESSED_DIR / "prices.csv"
if not _required_csv.exists():
    with st.status("Collecting initial data from ENTSO-E API...", expanded=True) as status:
        st.write("First launch detected — downloading 7 days of data. This may take a few minutes.")
        st.write("Make sure `ENTSOE_API_KEY` is set in your `.env` file.")
        try:
            collect_data()
            process_data()
            st.cache_data.clear()
            status.update(label="Initial data collection complete!", state="complete")
        except Exception as e:
            status.update(label="Data collection failed", state="error")
            st.error(f"Could not collect data: {e}")
            st.info("Check that `ENTSOE_API_KEY` is set in `.env` and that you have network access to the ENTSO-E API.")
            st.stop()

_ensure_refresh_thread()

# ── Load all data ───────────────────────────────────────────────────────────

try:
    prices = load_prices()
    load = load_load()
    generation = load_generation()
    forecast = load_wind_solar_forecast()
    capacity = load_installed_capacity()
    crossborder = load_crossborder()
except (FileNotFoundError, ValueError) as e:
    st.error(f"Data loading failed: {e}")
    st.info("Please ensure the ENTSO-E API key is configured and data has been collected.")
    st.stop()

# ── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.header("Data Refresh")
_price_csv = PROCESSED_DIR / "prices.csv"
if _price_csv.exists():
    _file_mtime = datetime.fromtimestamp(_price_csv.stat().st_mtime, tz=UTC)
    st.sidebar.text(f"Last data download:\n{_file_mtime:%Y-%m-%d %H:%M} UTC")
else:
    st.sidebar.text("Last data download: no data yet")
with _refresh_lock:
    in_progress = _refresh_in_progress
    last_error = _refresh_last_error
if in_progress:
    st.sidebar.info("Refresh in progress...")
if last_error:
    st.sidebar.warning(f"Last refresh failed: {last_error}")
st.sidebar.caption("Data auto-refreshes every 15 minutes.")
st.sidebar.markdown("---")
st.sidebar.header("Filters")

all_dates = prices.index
min_date = all_dates.min().date()
max_date = all_dates.max().date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Use exclusive end boundary (start of next day) for cleaner filtering
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt = pd.Timestamp(date_range[0], tz=all_dates.tz)
    end_dt = pd.Timestamp(date_range[1], tz=all_dates.tz) + pd.Timedelta(days=1)
else:
    start_dt = pd.Timestamp(min_date, tz=all_dates.tz)
    end_dt = pd.Timestamp(max_date, tz=all_dates.tz) + pd.Timedelta(days=1)

# Filter all dataframes
f_prices = filter_by_date(prices, start_dt, end_dt)
f_load = filter_by_date(load, start_dt, end_dt)
f_gen = filter_by_date(generation, start_dt, end_dt)
f_forecast = filter_by_date(forecast, start_dt, end_dt)
f_crossborder = {nb: filter_by_date(df, start_dt, end_dt) for nb, df in crossborder.items()}

# ── Tabs ────────────────────────────────────────────────────────────────────

tab_overview, tab_load, tab_gen, tab_capacity, tab_windsolar, tab_crossborder = st.tabs([
    "⚡ Overview", "🔌 Load Details", "🏭 Generation Details",
    "🔋 Installed Capacity", "🌿 Wind & Solar Details", "🔀 Cross-Border Details",
])

# ── Tab 1: Overview ─────────────────────────────────────────────────────────

with tab_overview:

    # ── KPIs ────────────────────────────────────────────────────────────────

    st.markdown("---")

    # Compute KPIs
    avg_price = f_prices[COL_PRICE].mean()
    peak_load_mw = f_load[COL_ACTUAL_LOAD].max()
    peak_load_gw = peak_load_mw / 1000

    total_gen = f_gen.sum()
    total_all = total_gen.sum()
    nuclear_pct = _safe_pct(total_gen[list(NUCLEAR_TYPES & set(f_gen.columns))].sum(), total_all)
    renewable_pct = _safe_pct(total_gen[list(RENEWABLE_TYPES & set(f_gen.columns))].sum(), total_all)

    net_imports = sum(df[COL_NET_IMPORT].mean() for df in f_crossborder.values())

    # Compute delta: compare first half vs second half of the selected period
    mid = f_prices.index[len(f_prices) // 2] if len(f_prices) > 1 else f_prices.index[0]
    first_half_price = f_prices.loc[f_prices.index < mid, COL_PRICE].mean()
    second_half_price = f_prices.loc[f_prices.index >= mid, COL_PRICE].mean()
    price_delta = second_half_price - first_half_price if pd.notna(first_half_price) and pd.notna(second_half_price) else None

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Avg Day-Ahead Price", f"{avg_price:.2f} EUR/MWh", delta=f"{price_delta:+.2f}" if price_delta is not None else None)
    col2.metric("Peak Load", f"{peak_load_gw:.1f} GW")
    col3.metric("Generation Mix", f"Nuc {nuclear_pct:.0f}% / Ren {renewable_pct:.0f}%")
    col4.metric("Net Import Balance", f"{net_imports:+,.0f} MW")

    # ── Section 1: Prices ──────────────────────────────────────────────────

    st.markdown("---")
    st.header("📈 Day-Ahead Prices")

    fig_prices = px.line(f_prices.reset_index(), x="timestamp", y=COL_PRICE, labels={COL_PRICE: "EUR/MWh", "timestamp": ""})
    fig_prices.update_layout(hovermode="x unified")
    st.plotly_chart(fig_prices, width="stretch", theme=None)

    # ── Section 2: Load ────────────────────────────────────────────────────

    st.header("🔌 Load: Actual vs Forecast")

    fig_load = go.Figure()
    fig_load.add_trace(go.Scatter(x=f_load.index, y=f_load[COL_ACTUAL_LOAD], name="Actual Load", mode="lines"))
    fig_load.add_trace(go.Scatter(x=f_load.index, y=f_load[COL_FORECAST_LOAD], name="Forecasted Load", mode="lines", line=dict(dash="dash")))
    fig_load.update_layout(yaxis_title="MW", hovermode="x unified")
    st.plotly_chart(fig_load, width="stretch", theme=None)

    # ── Section 3: Generation Mix ──────────────────────────────────────────

    st.header("🏭 Generation Mix")

    gen_col1, gen_col2 = st.columns([2, 1])

    with gen_col1:
        st.subheader("Generation Over Time")
        fig_gen = go.Figure()
        for col in f_gen.columns:
            color = SOURCE_COLORS.get(col)
            fig_gen.add_trace(go.Scatter(x=f_gen.index, y=f_gen[col], name=col, stackgroup="one", mode="lines", line=dict(color=color) if color else None))
        fig_gen.update_layout(yaxis_title="MW", hovermode="x unified")
        st.plotly_chart(fig_gen, width="stretch", theme=None)

    with gen_col2:
        st.subheader("Average Share by Source")
        avg_gen = f_gen.mean()
        avg_gen = avg_gen[avg_gen > 0].sort_values(ascending=False)
        fig_donut = px.pie(values=avg_gen.values, names=avg_gen.index, hole=0.4)
        fig_donut.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_donut, width="stretch", theme=None)

    # ── Section 4: Renewables ──────────────────────────────────────────────

    st.header("🌿 Renewables: Forecast vs Actual")

    ren_col1, ren_col2 = st.columns(2)

    with ren_col1:
        st.subheader("Wind & Solar: Forecast vs Actual")
        fig_ren = go.Figure()
        for src in ["Solar", "Wind Onshore", "Wind Offshore"]:
            color = SOURCE_COLORS.get(src)
            if src in f_gen.columns:
                fig_ren.add_trace(go.Scatter(x=f_gen.index, y=f_gen[src], name=f"{src} (actual)", mode="lines", line=dict(color=color) if color else None))
            if src in f_forecast.columns:
                fig_ren.add_trace(go.Scatter(x=f_forecast.index, y=f_forecast[src], name=f"{src} (forecast)", mode="lines", line=dict(dash="dash", color=color) if color else dict(dash="dash")))
        fig_ren.update_layout(yaxis_title="MW", hovermode="x unified")
        st.plotly_chart(fig_ren, width="stretch", theme=None)

    with ren_col2:
        st.subheader("Installed Capacity by Technology")
        cap = capacity.iloc[0] if len(capacity) > 0 else pd.Series(dtype=float)
        cap = cap[cap > 0].sort_values(ascending=True)
        fig_cap = px.bar(x=cap.values, y=cap.index, orientation="h", labels={"x": "MW", "y": ""})
        st.plotly_chart(fig_cap, width="stretch", theme=None)

    # ── Section 5: Cross-Border Flows ──────────────────────────────────────

    st.header("🔀 Cross-Border Flows")

    cb_col1, cb_col2 = st.columns([2, 1])

    with cb_col1:
        st.subheader("Net Imports Over Time (positive = import)")
        fig_cb = go.Figure()
        for nb in NEIGHBOURS:
            df_nb = f_crossborder[nb]
            label = NEIGHBOUR_LABELS.get(nb, nb)
            fig_cb.add_trace(go.Scatter(x=df_nb.index, y=df_nb[COL_NET_IMPORT], name=label, mode="lines"))
        fig_cb.update_layout(yaxis_title="MW", hovermode="x unified")
        st.plotly_chart(fig_cb, width="stretch", theme=None)

    with cb_col2:
        st.subheader("Total Energy Exchanged")
        summary_rows = []
        for nb in NEIGHBOURS:
            df_nb = f_crossborder[nb]
            total_import_gwh = _to_gwh(df_nb[COL_IMPORT].sum())
            total_export_gwh = _to_gwh(df_nb[COL_EXPORT].sum())
            net_gwh = total_import_gwh - total_export_gwh
            summary_rows.append({
                "Neighbour": NEIGHBOUR_LABELS.get(nb, nb),
                "Import (GWh)": round(total_import_gwh, 1),
                "Export (GWh)": round(total_export_gwh, 1),
                "Net (GWh)": round(net_gwh, 1),
            })
        summary_df = pd.DataFrame(summary_rows)
        st.dataframe(summary_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Tab 2: Load Details ─────────────────────────────────────────────────────

with tab_load:

    # ── Actual vs Forecast (larger) ────────────────────────────────────────

    st.header("🔌 Load: Actual vs Forecast")

    fig_load_detail = go.Figure()
    fig_load_detail.add_trace(go.Scatter(
        x=f_load.index, y=f_load[COL_ACTUAL_LOAD],
        name="Actual Load", mode="lines",
    ))
    fig_load_detail.add_trace(go.Scatter(
        x=f_load.index, y=f_load[COL_FORECAST_LOAD],
        name="Forecasted Load", mode="lines", line=dict(dash="dash"),
    ))
    fig_load_detail.update_layout(yaxis_title="MW", hovermode="x unified", height=500)
    st.plotly_chart(fig_load_detail, width="stretch", theme=None)

    # ── Forecast Error ─────────────────────────────────────────────────────

    st.header("📉 Forecast Error")

    forecast_error = f_load[COL_ACTUAL_LOAD] - f_load[COL_FORECAST_LOAD]

    fig_error = go.Figure()
    fig_error.add_trace(go.Scatter(
        x=f_load.index, y=forecast_error,
        name="Forecast Error", mode="lines",
        fill="tozeroy", fillcolor="rgba(204,85,0,0.15)",
    ))
    fig_error.add_hline(y=0, line_dash="dash", line_color=_hline_color, line_width=1)
    fig_error.update_layout(
        yaxis_title="MW (Actual - Forecast)",
        hovermode="x unified",
        height=400,
    )
    st.plotly_chart(fig_error, width="stretch", theme=None)

    # ── Daily Profile ──────────────────────────────────────────────────────

    st.header("🕐 Average Daily Profile")

    load_profile = f_load.copy()
    load_profile["hour"] = load_profile.index.hour
    hourly_avg = load_profile.groupby("hour")[[COL_ACTUAL_LOAD, COL_FORECAST_LOAD]].mean()

    fig_profile = go.Figure()
    fig_profile.add_trace(go.Scatter(
        x=hourly_avg.index, y=hourly_avg[COL_ACTUAL_LOAD],
        name="Actual Load", mode="lines+markers",
    ))
    fig_profile.add_trace(go.Scatter(
        x=hourly_avg.index, y=hourly_avg[COL_FORECAST_LOAD],
        name="Forecasted Load", mode="lines+markers", line=dict(dash="dash"),
    ))
    fig_profile.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="MW",
        hovermode="x unified",
        height=400,
        xaxis=dict(dtick=1),
    )
    st.plotly_chart(fig_profile, width="stretch", theme=None)

    # ── Statistics ─────────────────────────────────────────────────────────

    st.header("📊 Load Statistics")

    actual = f_load[COL_ACTUAL_LOAD]
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Min Load", f"{actual.min() / 1000:.1f} GW")
    kpi2.metric("Max Load", f"{actual.max() / 1000:.1f} GW")
    kpi3.metric("Mean Load", f"{actual.mean() / 1000:.1f} GW")
    kpi4.metric("Std Dev", f"{actual.std() / 1000:.2f} GW")

    stat_col1, stat_col2 = st.columns(2)

    with stat_col1:
        st.subheader("Load Distribution")
        fig_hist = px.histogram(
            x=actual, nbins=50,
            labels={"x": "Actual Load (MW)", "y": "Count"},
        )
        fig_hist.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_hist, width="stretch", theme=None)

    with stat_col2:
        st.subheader("Daily Summary")
        daily = f_load.resample("D").agg(
            Min_MW=(COL_ACTUAL_LOAD, "min"),
            Max_MW=(COL_ACTUAL_LOAD, "max"),
            Mean_MW=(COL_ACTUAL_LOAD, "mean"),
        )
        daily["Peak Hour"] = f_load[COL_ACTUAL_LOAD].groupby(f_load.index.date).apply(
            lambda s: s.idxmax().strftime("%H:%M") if len(s) > 0 else "-"
        ).values
        daily.index = daily.index.strftime("%Y-%m-%d")
        daily.index.name = "Date"
        for c in ["Min_MW", "Max_MW", "Mean_MW"]:
            daily[c] = daily[c].round(0).astype(int)
        daily.columns = ["Min (MW)", "Max (MW)", "Mean (MW)", "Peak Hour"]
        st.dataframe(daily, width="stretch")

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Tab 3: Generation Details ────────────────────────────────────────────────

with tab_gen:

    st.header("🏭 Generation Over Time")

    fig_gen_detail = go.Figure()
    for col in f_gen.columns:
        color = SOURCE_COLORS.get(col)
        fig_gen_detail.add_trace(go.Scatter(
            x=f_gen.index, y=f_gen[col], name=col, stackgroup="one", mode="lines",
            line=dict(color=color) if color else None,
        ))
    fig_gen_detail.update_layout(yaxis_title="MW", hovermode="x unified", height=500)
    st.plotly_chart(fig_gen_detail, width="stretch", theme=None)

    gen_d_col1, gen_d_col2 = st.columns(2)

    avg_gen_d = f_gen.mean()
    avg_gen_d = avg_gen_d[avg_gen_d > 0].sort_values(ascending=False)

    with gen_d_col1:
        st.subheader("Average Share by Source")
        fig_gen_donut = px.pie(values=avg_gen_d.values, names=avg_gen_d.index, hole=0.4)
        fig_gen_donut.update_traces(textposition="inside", textinfo="percent+label")
        fig_gen_donut.update_layout(height=500)
        st.plotly_chart(fig_gen_donut, width="stretch", theme=None)

    with gen_d_col2:
        st.subheader("Average Generation by Source")
        fig_gen_bar = px.bar(
            x=avg_gen_d.values, y=avg_gen_d.index, orientation="h",
            labels={"x": "MW", "y": ""},
        )
        fig_gen_bar.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_gen_bar, width="stretch", theme=None)

    st.header("📊 Generation Statistics")

    total_gen_all = f_gen.sum()
    total_all_mw = total_gen_all.sum()
    total_gwh = _to_gwh(total_all_mw)
    nuc_pct = _safe_pct(total_gen_all[list(NUCLEAR_TYPES & set(f_gen.columns))].sum(), total_all_mw)
    ren_pct = _safe_pct(total_gen_all[list(RENEWABLE_TYPES & set(f_gen.columns))].sum(), total_all_mw)

    gk1, gk2, gk3 = st.columns(3)
    gk1.metric("Total Generation", f"{total_gwh:.1f} GWh")
    gk2.metric("Nuclear Share", f"{nuc_pct:.1f}%")
    gk3.metric("Renewable Share", f"{ren_pct:.1f}%")

    st.subheader("Daily Generation Summary")
    daily_gen = f_gen.resample("D").sum().apply(_to_gwh)
    daily_total = daily_gen.sum(axis=1)
    daily_nuc = daily_gen[list(NUCLEAR_TYPES & set(f_gen.columns))].sum(axis=1)
    daily_ren = daily_gen[list(RENEWABLE_TYPES & set(f_gen.columns))].sum(axis=1)
    daily_gen_summary = pd.DataFrame({
        "Total (GWh)": daily_total.round(1),
        "Nuclear (%)": (daily_nuc / daily_total * 100).round(1),
        "Renewable (%)": (daily_ren / daily_total * 100).round(1),
    })
    daily_gen_summary.index = daily_gen_summary.index.strftime("%Y-%m-%d")
    daily_gen_summary.index.name = "Date"
    st.dataframe(daily_gen_summary, width="stretch")

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Tab 4: Installed Capacity ────────────────────────────────────────────────

with tab_capacity:

    cap_data = capacity.iloc[0] if len(capacity) > 0 else pd.Series(dtype=float)
    cap_data = cap_data[cap_data > 0].sort_values(ascending=True)

    cap_col1, cap_col2 = st.columns(2)

    with cap_col1:
        st.header("🔋 Installed Capacity by Technology")
        fig_cap_bar = px.bar(
            x=cap_data.values, y=cap_data.index, orientation="h",
            labels={"x": "MW", "y": ""},
        )
        fig_cap_bar.update_layout(height=500)
        st.plotly_chart(fig_cap_bar, width="stretch", theme=None)

    with cap_col2:
        st.header("Capacity Share")
        fig_cap_donut = px.pie(values=cap_data.values, names=cap_data.index, hole=0.4)
        fig_cap_donut.update_traces(textposition="inside", textinfo="percent+label")
        fig_cap_donut.update_layout(height=500)
        st.plotly_chart(fig_cap_donut, width="stretch", theme=None)

    st.header("⚙️ Capacity vs Average Generation")

    avg_gen_cap = f_gen.mean()
    common_types = sorted(set(cap_data.index) & set(avg_gen_cap.index))
    if common_types:
        cap_vs_gen = pd.DataFrame({
            "Installed Capacity (MW)": cap_data[common_types].values,
            "Average Generation (MW)": avg_gen_cap[common_types].values,
        }, index=common_types)

        fig_cap_vs_gen = go.Figure()
        fig_cap_vs_gen.add_trace(go.Bar(
            y=common_types, x=cap_vs_gen["Installed Capacity (MW)"],
            name="Installed Capacity", orientation="h",
        ))
        fig_cap_vs_gen.add_trace(go.Bar(
            y=common_types, x=cap_vs_gen["Average Generation (MW)"],
            name="Average Generation", orientation="h",
        ))
        fig_cap_vs_gen.update_layout(
            barmode="group", xaxis_title="MW", height=500, hovermode="y unified",
        )
        st.plotly_chart(fig_cap_vs_gen, width="stretch", theme=None)

    st.header("📊 Capacity Statistics")

    total_cap_gw = cap_data.sum() / 1000
    top3 = cap_data.sort_values(ascending=False).head(3)
    top3_str = ", ".join(f"{t} ({v / 1000:.1f} GW)" for t, v in top3.items())

    ck1, ck2 = st.columns(2)
    ck1.metric("Total Installed Capacity", f"{total_cap_gw:.1f} GW")
    ck2.metric("Top Technologies", top3_str)

    st.subheader("Capacity Factor by Technology")
    if common_types:
        cf_data = []
        for t in common_types:
            installed = cap_data[t]
            avg_actual = avg_gen_cap[t]
            cf = _safe_pct(avg_actual, installed)
            cf_data.append({
                "Technology": t,
                "Installed (MW)": round(installed, 0),
                "Avg Generation (MW)": round(avg_actual, 0),
                "Capacity Factor (%)": round(cf, 1),
            })
        cf_df = pd.DataFrame(cf_data).sort_values("Capacity Factor (%)", ascending=False)
        st.dataframe(cf_df, width="stretch", hide_index=True)

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Tab 5: Wind & Solar Details ──────────────────────────────────────────────

with tab_windsolar:

    st.header("🌿 Forecast vs Actual by Source")

    ws_sources = ["Solar", "Wind Onshore", "Wind Offshore"]
    ws_cols = st.columns(len(ws_sources))

    for ws_col, src in zip(ws_cols, ws_sources):
        with ws_col:
            st.subheader(src)
            fig_ws = go.Figure()
            color = SOURCE_COLORS.get(src)
            if src in f_gen.columns:
                fig_ws.add_trace(go.Scatter(
                    x=f_gen.index, y=f_gen[src], name="Actual", mode="lines",
                    line=dict(color=color) if color else None,
                ))
            if src in f_forecast.columns:
                fig_ws.add_trace(go.Scatter(
                    x=f_forecast.index, y=f_forecast[src], name="Forecast", mode="lines",
                    line=dict(dash="dash", color=color) if color else dict(dash="dash"),
                ))
            fig_ws.update_layout(yaxis_title="MW", hovermode="x unified", height=350)
            st.plotly_chart(fig_ws, width="stretch", theme=None)

    st.header("📉 Forecast Error (Actual - Forecast)")

    fig_ws_error = go.Figure()
    for src in ws_sources:
        if src in f_gen.columns and src in f_forecast.columns:
            common_idx = f_gen.index.intersection(f_forecast.index)
            error = f_gen.loc[common_idx, src] - f_forecast.loc[common_idx, src]
            color = SOURCE_COLORS.get(src)
            fig_ws_error.add_trace(go.Scatter(
                x=common_idx, y=error, name=src, mode="lines",
                line=dict(color=color) if color else None,
            ))
    fig_ws_error.add_hline(y=0, line_dash="dash", line_color=_hline_color, line_width=1)
    fig_ws_error.update_layout(yaxis_title="MW", hovermode="x unified", height=400)
    st.plotly_chart(fig_ws_error, width="stretch", theme=None)

    st.header("🕐 Average Daily Profile")

    fig_ws_profile = go.Figure()
    for src in ws_sources:
        if src in f_gen.columns:
            hourly = f_gen[src].groupby(f_gen.index.hour).mean()
            color = SOURCE_COLORS.get(src)
            fig_ws_profile.add_trace(go.Scatter(
                x=hourly.index, y=hourly.values, name=src, mode="lines+markers",
                line=dict(color=color) if color else None,
            ))
    fig_ws_profile.update_layout(
        xaxis_title="Hour of Day", yaxis_title="MW",
        hovermode="x unified", height=400, xaxis=dict(dtick=1),
    )
    st.plotly_chart(fig_ws_profile, width="stretch", theme=None)

    st.header("📊 Wind & Solar Statistics")

    ws_total_gwh = 0
    ws_metrics = []
    for src in ws_sources:
        if src in f_gen.columns:
            src_gwh = _to_gwh(f_gen[src].sum())
            ws_total_gwh += src_gwh
            src_cap = cap_data[src] if src in cap_data.index else 0
            cf = _safe_pct(f_gen[src].mean(), src_cap)
            ws_metrics.append((src, src_gwh, cf))

    wk_cols = st.columns(1 + len(ws_metrics))
    wk_cols[0].metric("Total Renewable Generation", f"{ws_total_gwh:.1f} GWh")
    for i, (src, gwh, cf) in enumerate(ws_metrics):
        wk_cols[i + 1].metric(f"{src} CF", f"{cf:.1f}%")

    st.subheader("Daily Summary")
    daily_ws_rows = []
    for src in ws_sources:
        if src in f_gen.columns:
            daily_src = f_gen[src].resample("D").sum().apply(_to_gwh)
            for date, val in daily_src.items():
                daily_ws_rows.append({"Date": date.strftime("%Y-%m-%d"), "Source": src, "GWh": round(val, 2)})
    if daily_ws_rows:
        daily_ws_df = pd.DataFrame(daily_ws_rows).pivot(index="Date", columns="Source", values="GWh")
        daily_ws_df["Total"] = daily_ws_df.sum(axis=1).round(2)
        st.dataframe(daily_ws_df, width="stretch")

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Tab 6: Cross-Border Details ──────────────────────────────────────────────

with tab_crossborder:

    st.header("🔀 Net Imports Over Time")

    fig_cb_detail = go.Figure()
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        label = NEIGHBOUR_LABELS.get(nb, nb)
        fig_cb_detail.add_trace(go.Scatter(
            x=df_nb.index, y=df_nb[COL_NET_IMPORT], name=label, mode="lines",
        ))
    fig_cb_detail.add_hline(y=0, line_dash="dash", line_color=_hline_color, line_width=1)
    fig_cb_detail.update_layout(
        yaxis_title="MW (positive = import)", hovermode="x unified", height=500,
    )
    st.plotly_chart(fig_cb_detail, width="stretch", theme=None)

    st.header("📊 Import & Export per Neighbour")

    for row_start in range(0, len(NEIGHBOURS), 3):
        row_nbs = NEIGHBOURS[row_start:row_start + 3]
        cols = st.columns(len(row_nbs))
        for col, nb in zip(cols, row_nbs):
            with col:
                label = NEIGHBOUR_LABELS.get(nb, nb)
                st.subheader(label)
                df_nb = f_crossborder[nb]
                fig_nb = go.Figure()
                fig_nb.add_trace(go.Scatter(
                    x=df_nb.index, y=df_nb[COL_IMPORT], name="Import", mode="lines",
                    line=dict(color="#2299DD"),
                ))
                fig_nb.add_trace(go.Scatter(
                    x=df_nb.index, y=df_nb[COL_EXPORT], name="Export", mode="lines",
                    line=dict(color="#F57C00"),
                ))
                fig_nb.add_trace(go.Scatter(
                    x=df_nb.index, y=df_nb[COL_NET_IMPORT], name="Net Import", mode="lines",
                    line=dict(color=_hline_color, dash="dash"),
                ))
                fig_nb.update_layout(
                    yaxis_title="MW", hovermode="x unified", height=350,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_nb, width="stretch", theme=None)

    st.header("📅 Daily Net Import by Neighbour")

    daily_net_rows = []
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        daily_net = df_nb[COL_NET_IMPORT].resample("D").sum().apply(_to_gwh)
        label = NEIGHBOUR_LABELS.get(nb, nb)
        for date, val in daily_net.items():
            daily_net_rows.append({"Date": date, "Neighbour": label, "Net Import (GWh)": val})

    if daily_net_rows:
        daily_net_df = pd.DataFrame(daily_net_rows)
        fig_daily_net = px.bar(
            daily_net_df, x="Date", y="Net Import (GWh)", color="Neighbour",
            barmode="relative",
        )
        fig_daily_net.update_layout(hovermode="x unified", height=500)
        st.plotly_chart(fig_daily_net, width="stretch", theme=None)

    st.header("⚡ Total Energy Exchanged")

    exchange_rows = []
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        label = NEIGHBOUR_LABELS.get(nb, nb)
        imp_gwh = _to_gwh(df_nb[COL_IMPORT].sum())
        exp_gwh = _to_gwh(df_nb[COL_EXPORT].sum())
        exchange_rows.append({"Neighbour": label, "Direction": "Import", "GWh": imp_gwh})
        exchange_rows.append({"Neighbour": label, "Direction": "Export", "GWh": exp_gwh})

    if exchange_rows:
        exchange_df = pd.DataFrame(exchange_rows)
        fig_exchange = px.bar(
            exchange_df, x="GWh", y="Neighbour", color="Direction",
            orientation="h", barmode="group",
            color_discrete_map={"Import": "#2299DD", "Export": "#F57C00"},
        )
        fig_exchange.update_layout(height=400, hovermode="y unified")
        st.plotly_chart(fig_exchange, width="stretch", theme=None)

    st.header("📊 Cross-Border Statistics")

    nb_net_gwh = {}
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        label = NEIGHBOUR_LABELS.get(nb, nb)
        nb_net_gwh[label] = _to_gwh(df_nb[COL_IMPORT].sum() - df_nb[COL_EXPORT].sum())

    total_net_gwh = sum(nb_net_gwh.values())
    largest_importer = max(nb_net_gwh, key=nb_net_gwh.get)
    largest_exporter = min(nb_net_gwh, key=nb_net_gwh.get)

    cbk1, cbk2, cbk3 = st.columns(3)
    cbk1.metric("Total Net Import", f"{total_net_gwh:+.1f} GWh")
    cbk2.metric("Largest Net Importer", f"{largest_importer} ({nb_net_gwh[largest_importer]:+.1f} GWh)")
    cbk3.metric("Largest Net Exporter", f"{largest_exporter} ({nb_net_gwh[largest_exporter]:+.1f} GWh)")

    st.subheader("Daily Net Import Summary (GWh)")

    daily_summary_rows = []
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        label = NEIGHBOUR_LABELS.get(nb, nb)
        daily_net = df_nb[COL_NET_IMPORT].resample("D").sum().apply(_to_gwh)
        for date, val in daily_net.items():
            daily_summary_rows.append({"Date": date.strftime("%Y-%m-%d"), "Neighbour": label, "GWh": round(val, 2)})

    if daily_summary_rows:
        daily_cb_df = pd.DataFrame(daily_summary_rows).pivot(index="Date", columns="Neighbour", values="GWh")
        daily_cb_df["Total"] = daily_cb_df.sum(axis=1).round(2)
        st.dataframe(daily_cb_df, width="stretch")

    st.markdown("---")
    st.caption("Data source: ENTSO-E Transparency Platform • Dashboard built with Streamlit & Plotly")

# ── Auto-refresh: rerun when new data is available ───────────────────────────

with _refresh_lock:
    current_update = _last_data_update

if current_update > st.session_state.get("_last_seen_update", 0.0):
    # New data arrived — update session state and rerun immediately
    st.session_state._last_seen_update = current_update
    st.rerun()
else:
    # No new data yet — poll again after POLL_INTERVAL_SECONDS
    time.sleep(POLL_INTERVAL_SECONDS)
    st.rerun()
