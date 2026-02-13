"""Streamlit dashboard for France ENTSO-E energy data."""

import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from entsoe_ai_warriors.collect_france import main as collect_data

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

REFRESH_INTERVAL_SECONDS = 15 * 60  # 15 minutes

logger = logging.getLogger(__name__)

# Shared state for the background thread (module-level, survives Streamlit reruns)
_refresh_lock = threading.Lock()
_refresh_in_progress = False


def _refresh_loop() -> None:
    """Background loop: collect fresh data every 15 minutes."""
    global _refresh_in_progress
    while True:
        try:
            with _refresh_lock:
                _refresh_in_progress = True
            logger.info("Starting data refresh from ENTSO-E API...")
            collect_data()
            st.cache_data.clear()
            with _refresh_lock:
                _refresh_in_progress = False
            logger.info("Data refresh completed")
        except Exception:
            with _refresh_lock:
                _refresh_in_progress = False
            logger.exception("Data refresh failed")
        time.sleep(REFRESH_INTERVAL_SECONDS)


def _ensure_refresh_thread() -> None:
    """Start the background refresh thread once per process."""
    if "refresh_thread_started" not in st.session_state:
        thread = threading.Thread(target=_refresh_loop, daemon=True)
        thread.start()
        st.session_state.refresh_thread_started = True

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


# ── Data loading ────────────────────────────────────────────────────────────


@st.cache_data
def load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_day_ahead_prices.csv", index_col=0, parse_dates=True)
    df.columns = ["Price"]
    df.index.name = "timestamp"
    return df


@st.cache_data
def load_load() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_load.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    return df


@st.cache_data
def load_generation() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_generation_by_type.csv", header=[0, 1], index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    # Keep only "Actual Aggregated" columns and flatten
    agg_cols = [(t, sub) for t, sub in df.columns if sub == "Actual Aggregated"]
    df_agg = df[agg_cols].copy()
    df_agg.columns = [t for t, _ in df_agg.columns]
    return df_agg


@st.cache_data
def load_wind_solar_forecast() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_wind_solar_forecast.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    return df


@st.cache_data
def load_installed_capacity() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_installed_capacity.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    return df


@st.cache_data
def load_crossborder() -> dict[str, pd.DataFrame]:
    flows: dict[str, pd.DataFrame] = {}
    for nb in NEIGHBOURS:
        export_path = DATA_DIR / f"france_crossborder_FR_to_{nb}.csv"
        import_path = DATA_DIR / f"france_crossborder_{nb}_to_FR.csv"
        exp = pd.read_csv(export_path, index_col=0, parse_dates=True)
        imp = pd.read_csv(import_path, index_col=0, parse_dates=True)
        exp.columns = ["Export"]
        imp.columns = ["Import"]
        combined = imp.join(exp, how="outer")
        combined["Net Import"] = combined["Import"] - combined["Export"]
        combined.index.name = "timestamp"
        flows[nb] = combined
    return flows


# ── Helpers ─────────────────────────────────────────────────────────────────


def filter_by_date(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    mask = (df.index >= start) & (df.index <= end)
    return df.loc[mask]


# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="France Energy Dashboard", page_icon="⚡", layout="wide")
_ensure_refresh_thread()
st.title("⚡ France Energy Dashboard — ENTSO-E Data")

# ── Load all data ───────────────────────────────────────────────────────────

prices = load_prices()
load = load_load()
generation = load_generation()
forecast = load_wind_solar_forecast()
capacity = load_installed_capacity()
crossborder = load_crossborder()

# ── Sidebar ─────────────────────────────────────────────────────────────────

st.sidebar.header("Data Refresh")
# Show file-based last download time (survives app restarts)
_price_csv = DATA_DIR / "france_day_ahead_prices.csv"
if _price_csv.exists():
    _file_mtime = datetime.fromtimestamp(_price_csv.stat().st_mtime, tz=UTC)
    st.sidebar.text(f"Last data download:\n{_file_mtime:%Y-%m-%d %H:%M} UTC")
else:
    st.sidebar.text("Last data download: no data yet")
with _refresh_lock:
    in_progress = _refresh_in_progress
if in_progress:
    st.sidebar.info("Refresh in progress...")
st.sidebar.caption("Data auto-refreshes every 15 min.")
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

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt = pd.Timestamp(date_range[0], tz=all_dates.tz)
    end_dt = pd.Timestamp(date_range[1], tz=all_dates.tz) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    start_dt = pd.Timestamp(min_date, tz=all_dates.tz)
    end_dt = pd.Timestamp(max_date, tz=all_dates.tz) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

# Filter all dataframes
f_prices = filter_by_date(prices, start_dt, end_dt)
f_load = filter_by_date(load, start_dt, end_dt)
f_gen = filter_by_date(generation, start_dt, end_dt)
f_forecast = filter_by_date(forecast, start_dt, end_dt)
f_crossborder = {nb: filter_by_date(df, start_dt, end_dt) for nb, df in crossborder.items()}

# ── KPIs ────────────────────────────────────────────────────────────────────

st.markdown("---")

# Compute KPIs
avg_price = f_prices["Price"].mean()
peak_load_mw = f_load["Actual Load"].max()
peak_load_gw = peak_load_mw / 1000

total_gen = f_gen.sum()
total_all = total_gen.sum()
nuclear_pct = total_gen[list(NUCLEAR_TYPES & set(f_gen.columns))].sum() / total_all * 100 if total_all > 0 else 0
renewable_pct = total_gen[list(RENEWABLE_TYPES & set(f_gen.columns))].sum() / total_all * 100 if total_all > 0 else 0

net_imports = sum(df["Net Import"].mean() for df in f_crossborder.values())

# Compute delta: compare first half vs second half of the selected period
mid = f_prices.index[len(f_prices) // 2] if len(f_prices) > 1 else f_prices.index[0]
first_half_price = f_prices.loc[f_prices.index < mid, "Price"].mean()
second_half_price = f_prices.loc[f_prices.index >= mid, "Price"].mean()
price_delta = second_half_price - first_half_price if pd.notna(first_half_price) and pd.notna(second_half_price) else None

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Day-Ahead Price", f"{avg_price:.2f} EUR/MWh", delta=f"{price_delta:+.2f}" if price_delta is not None else None)
col2.metric("Peak Load", f"{peak_load_gw:.1f} GW")
col3.metric("Generation Mix", f"Nuc {nuclear_pct:.0f}% / Ren {renewable_pct:.0f}%")
col4.metric("Net Import Balance", f"{net_imports:+,.0f} MW")

# ── Section 1: Prices ──────────────────────────────────────────────────────

st.markdown("---")
st.header("📈 Day-Ahead Prices")

fig_prices = px.line(f_prices.reset_index(), x="timestamp", y="Price", labels={"Price": "EUR/MWh", "timestamp": ""})
fig_prices.update_layout(hovermode="x unified")
st.plotly_chart(fig_prices, width="stretch")

# ── Section 2: Load ────────────────────────────────────────────────────────

st.header("🔌 Load: Actual vs Forecast")

fig_load = go.Figure()
fig_load.add_trace(go.Scatter(x=f_load.index, y=f_load["Actual Load"], name="Actual Load", mode="lines"))
fig_load.add_trace(go.Scatter(x=f_load.index, y=f_load["Forecasted Load"], name="Forecasted Load", mode="lines", line=dict(dash="dash")))
fig_load.update_layout(yaxis_title="MW", hovermode="x unified")
st.plotly_chart(fig_load, width="stretch")

# ── Section 3: Generation Mix ──────────────────────────────────────────────

st.header("🏭 Generation Mix")

gen_col1, gen_col2 = st.columns([2, 1])

with gen_col1:
    st.subheader("Generation Over Time")
    fig_gen = go.Figure()
    for col in f_gen.columns:
        fig_gen.add_trace(go.Scatter(x=f_gen.index, y=f_gen[col], name=col, stackgroup="one", mode="lines"))
    fig_gen.update_layout(yaxis_title="MW", hovermode="x unified")
    st.plotly_chart(fig_gen, width="stretch")

with gen_col2:
    st.subheader("Average Share by Source")
    avg_gen = f_gen.mean()
    avg_gen = avg_gen[avg_gen > 0].sort_values(ascending=False)
    fig_donut = px.pie(values=avg_gen.values, names=avg_gen.index, hole=0.4)
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_donut, width="stretch")

# ── Section 4: Renewables ──────────────────────────────────────────────────

st.header("🌿 Renewables: Forecast vs Actual")

ren_col1, ren_col2 = st.columns(2)

with ren_col1:
    st.subheader("Wind & Solar: Forecast vs Actual")
    fig_ren = go.Figure()
    for src in ["Solar", "Wind Onshore", "Wind Offshore"]:
        if src in f_gen.columns:
            fig_ren.add_trace(go.Scatter(x=f_gen.index, y=f_gen[src], name=f"{src} (actual)", mode="lines"))
        if src in f_forecast.columns:
            fig_ren.add_trace(go.Scatter(x=f_forecast.index, y=f_forecast[src], name=f"{src} (forecast)", mode="lines", line=dict(dash="dash")))
    fig_ren.update_layout(yaxis_title="MW", hovermode="x unified")
    st.plotly_chart(fig_ren, width="stretch")

with ren_col2:
    st.subheader("Installed Capacity by Technology")
    cap = capacity.iloc[0] if len(capacity) > 0 else pd.Series(dtype=float)
    cap = cap[cap > 0].sort_values(ascending=True)
    fig_cap = px.bar(x=cap.values, y=cap.index, orientation="h", labels={"x": "MW", "y": ""})
    st.plotly_chart(fig_cap, width="stretch")

# ── Section 5: Cross-Border Flows ──────────────────────────────────────────

st.header("🔀 Cross-Border Flows")

cb_col1, cb_col2 = st.columns([2, 1])

with cb_col1:
    st.subheader("Net Imports Over Time (positive = import)")
    fig_cb = go.Figure()
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        label = NEIGHBOUR_LABELS.get(nb, nb)
        fig_cb.add_trace(go.Scatter(x=df_nb.index, y=df_nb["Net Import"], name=label, mode="lines"))
    fig_cb.update_layout(yaxis_title="MW", hovermode="x unified")
    st.plotly_chart(fig_cb, width="stretch")

with cb_col2:
    st.subheader("Total Energy Exchanged")
    summary_rows = []
    for nb in NEIGHBOURS:
        df_nb = f_crossborder[nb]
        # Convert MW 15-min data to GWh: sum(MW) * 0.25h / 1000
        total_import_gwh = df_nb["Import"].sum() * 0.25 / 1000
        total_export_gwh = df_nb["Export"].sum() * 0.25 / 1000
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
