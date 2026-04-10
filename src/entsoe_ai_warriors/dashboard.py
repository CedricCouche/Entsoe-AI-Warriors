import logging
import threading
import time

import pandas as pd
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFRESH_INTERVAL_SECONDS = 900
POLL_INTERVAL_SECONDS = 30
INTERVAL_HOURS = 0.25
MW_TO_GWH = INTERVAL_HOURS / 1000

NEIGHBOURS = ["BE", "CH", "DE_LU", "ES", "GB", "IT_NORD"]

RENEWABLE_TYPES = [
    "Solar",
    "Wind Offshore",
    "Wind Onshore",
    "Hydro Run-of-river and poundage",
    "Hydro Water Reservoir",
]
NUCLEAR_TYPES = ["Nuclear"]

# ---------------------------------------------------------------------------
# Adalan theme
# ---------------------------------------------------------------------------

ADALAN_COLORS = [
    "#2299DD",  # Primary blue
    "#F57C00",  # Orange accent
    "#00ACC1",  # Teal
    "#43A047",  # Green
    "#8E24AA",  # Purple
    "#E53935",  # Red
    "#FB8C00",  # Amber
    "#3949AB",  # Indigo
]

SOURCE_COLORS = {
    "Solar": "#F57C00",
    "Hydro Pumped Storage": "#2299DD",
    "Hydro Run-of-river and poundage": "#00ACC1",
    "Hydro Water Reservoir": "#3949AB",
}

pio.templates["adalan"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="'Inter', 'Segoe UI', Arial, sans-serif", color="#1A2940"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F4F7FB",
        colorway=ADALAN_COLORS,
        xaxis=dict(gridcolor="rgba(34,153,221,0.12)", showgrid=True),
        yaxis=dict(gridcolor="rgba(34,153,221,0.12)", showgrid=True),
    )
)
pio.templates.default = "adalan"

# ---------------------------------------------------------------------------
# Background refresh state (module-level, shared across Streamlit reruns)
# ---------------------------------------------------------------------------

_refresh_lock = threading.Lock()
_last_data_update: pd.Timestamp | None = None
_refresh_last_error: str | None = None
_refresh_in_progress: bool = False


def _refresh_loop() -> None:
    global _last_data_update, _refresh_last_error, _refresh_in_progress
    while True:
        with _refresh_lock:
            _refresh_in_progress = True
        try:
            collect_data()
            process_data()
            with _refresh_lock:
                _last_data_update = pd.Timestamp.now()
                _refresh_last_error = None
            st.cache_data.clear()
        except Exception as exc:
            with _refresh_lock:
                _refresh_last_error = str(exc)
            logger.exception("Background refresh failed")
        finally:
            with _refresh_lock:
                _refresh_in_progress = False
        time.sleep(REFRESH_INTERVAL_SECONDS)


def _ensure_refresh_thread() -> None:
    if not st.session_state.get("refresh_thread_started"):
        t = threading.Thread(target=_refresh_loop, daemon=True)
        t.start()
        st.session_state["refresh_thread_started"] = True


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@st.cache_data
def load_prices() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "prices.csv", index_col=0, parse_dates=True)


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
    result: dict[str, pd.DataFrame] = {}
    for nb in NEIGHBOURS:
        path = PROCESSED_DIR / f"crossborder_{nb}.csv"
        if path.exists():
            result[nb] = pd.read_csv(path, index_col=0, parse_dates=True)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_pct(numerator: float, denominator: float) -> float:
    if not denominator or pd.isna(denominator):
        return 0.0
    return numerator / denominator * 100


def _to_gwh(mw_sum: float) -> float:
    return mw_sum * MW_TO_GWH


def filter_by_date(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty:
        return df
    if df.index.tz is not None and start.tzinfo is None:
        start = start.tz_localize("UTC")
        end = end.tz_localize("UTC")
    return df[(df.index >= start) & (df.index < end)]


def _color_map(sources) -> dict[str, str]:
    colors: dict[str, str] = {}
    palette_idx = 0
    for src in sources:
        if src in SOURCE_COLORS:
            colors[src] = SOURCE_COLORS[src]
        else:
            colors[src] = ADALAN_COLORS[palette_idx % len(ADALAN_COLORS)]
            palette_idx += 1
    return colors


# ---------------------------------------------------------------------------
# Tab 1 — Overview
# ---------------------------------------------------------------------------

def _render_overview(
    prices_df: pd.DataFrame,
    load_df: pd.DataFrame,
    gen_df: pd.DataFrame,
    wsf_df: pd.DataFrame,
    cap_df: pd.DataFrame,
    cb_dict: dict[str, pd.DataFrame],
) -> None:
    # KPIs
    avg_price = prices_df[COL_PRICE].mean() if not prices_df.empty else 0.0
    peak_load = load_df[COL_ACTUAL_LOAD].max() if not load_df.empty else 0.0
    total_gen_gwh = _to_gwh(gen_df.sum().sum()) if not gen_df.empty else 0.0
    ren_cols = [c for c in gen_df.columns if c in RENEWABLE_TYPES]
    ren_sum = gen_df[ren_cols].sum().sum() if ren_cols else 0.0
    total_sum = gen_df.sum().sum() if not gen_df.empty else 0.0
    ren_share = _safe_pct(ren_sum, total_sum)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg Price", f"{avg_price:.1f} €/MWh")
    c2.metric("Peak Load", f"{peak_load:,.0f} MW")
    c3.metric("Total Generation", f"{total_gen_gwh:,.1f} GWh")
    c4.metric("Renewable Share", f"{ren_share:.1f} %")

    # Day-ahead prices
    if not prices_df.empty:
        fig = go.Figure(go.Scatter(
            x=prices_df.index, y=prices_df[COL_PRICE],
            mode="lines", name="Price", line=dict(color=ADALAN_COLORS[0])
        ))
        fig.update_layout(title="Day-Ahead Prices (€/MWh)", template="adalan",
                          xaxis_title="", yaxis_title="€/MWh")
        st.plotly_chart(fig, use_container_width=True)

    # Load actual vs forecast
    if not load_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=load_df.index, y=load_df[COL_ACTUAL_LOAD],
                                 mode="lines", name="Actual", line=dict(color=ADALAN_COLORS[0])))
        fig.add_trace(go.Scatter(x=load_df.index, y=load_df[COL_FORECAST_LOAD],
                                 mode="lines", name="Forecast", line=dict(color=ADALAN_COLORS[1], dash="dash")))
        fig.update_layout(title="Load: Actual vs Forecast (MW)", template="adalan",
                          xaxis_title="", yaxis_title="MW")
        st.plotly_chart(fig, use_container_width=True)

    # Generation mix: stacked area + donut
    if not gen_df.empty:
        cmap = _color_map(gen_df.columns)
        idx_name = gen_df.index.name or "timestamp"
        df_m = gen_df.reset_index().melt(id_vars=idx_name, var_name="Source", value_name="MW")

        col1, col2 = st.columns([2, 1])
        with col1:
            fig = go.Figure()
            for src in gen_df.columns:
                src_data = df_m[df_m["Source"] == src]
                fig.add_trace(go.Scatter(
                    x=src_data[idx_name], y=src_data["MW"],
                    name=src, stackgroup="one", mode="lines",
                    line=dict(width=0), fillcolor=cmap.get(src, ADALAN_COLORS[0]),
                ))
            fig.update_layout(title="Generation Mix (MW)", template="adalan",
                               xaxis_title="", yaxis_title="MW")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            avg_mw = gen_df.mean().sort_values(ascending=False)
            fig = go.Figure(go.Pie(
                labels=avg_mw.index, values=avg_mw.values, hole=0.4,
                marker=dict(colors=[cmap.get(s, ADALAN_COLORS[0]) for s in avg_mw.index]),
            ))
            fig.update_layout(title="Generation Mix (avg MW)", template="adalan")
            st.plotly_chart(fig, use_container_width=True)

    # Renewables forecast vs actual
    if not wsf_df.empty and not gen_df.empty:
        ren_actual_cols = [c for c in gen_df.columns if c in RENEWABLE_TYPES]
        fcast_cols = [c for c in wsf_df.columns if any(s in c for s in ["Solar", "Wind"])]
        if ren_actual_cols and fcast_cols:
            actual_ren = gen_df[ren_actual_cols].sum(axis=1)
            fcast_ren = wsf_df[fcast_cols].sum(axis=1)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=actual_ren.index, y=actual_ren.values,
                                     mode="lines", name="Actual", line=dict(color=ADALAN_COLORS[3])))
            fig.add_trace(go.Scatter(x=fcast_ren.index, y=fcast_ren.values,
                                     mode="lines", name="Forecast", line=dict(color=ADALAN_COLORS[2], dash="dash")))
            fig.update_layout(title="Renewables: Forecast vs Actual (MW)", template="adalan",
                               xaxis_title="", yaxis_title="MW")
            st.plotly_chart(fig, use_container_width=True)

    # Installed capacity
    if not cap_df.empty:
        latest = cap_df.iloc[-1].dropna().sort_values(ascending=True)
        latest = latest[latest > 0]
        cmap_cap = _color_map(latest.index)
        fig = go.Figure(go.Bar(
            x=latest.values, y=latest.index, orientation="h",
            marker_color=[cmap_cap.get(s, ADALAN_COLORS[0]) for s in latest.index],
        ))
        fig.update_layout(title="Installed Capacity (MW)", template="adalan",
                          xaxis_title="MW", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # Cross-border net flows
    if cb_dict:
        net_all = pd.DataFrame({
            nb: df[COL_NET_IMPORT] for nb, df in cb_dict.items() if COL_NET_IMPORT in df.columns
        })
        if not net_all.empty:
            fig = go.Figure()
            for i, nb in enumerate(net_all.columns):
                fig.add_trace(go.Scatter(
                    x=net_all.index, y=net_all[nb], mode="lines", name=nb,
                    line=dict(color=ADALAN_COLORS[i % len(ADALAN_COLORS)]),
                ))
            fig.update_layout(title="Cross-Border Net Flows (MW, positive = import)",
                               template="adalan", xaxis_title="", yaxis_title="MW")
            st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 2 — Load Details
# ---------------------------------------------------------------------------

def _render_load_details(load_df: pd.DataFrame) -> None:
    if load_df.empty:
        st.warning("No load data available.")
        return

    df = load_df.copy()

    # Large actual vs forecast
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[COL_ACTUAL_LOAD],
                             mode="lines", name="Actual", line=dict(color=ADALAN_COLORS[0])))
    fig.add_trace(go.Scatter(x=df.index, y=df[COL_FORECAST_LOAD],
                             mode="lines", name="Forecast", line=dict(color=ADALAN_COLORS[1], dash="dash")))
    fig.update_layout(title="Load: Actual vs Forecast (MW)", template="adalan",
                      height=450, xaxis_title="", yaxis_title="MW")
    st.plotly_chart(fig, use_container_width=True)

    # Forecast error (filled to zero)
    df["Forecast Error"] = df[COL_ACTUAL_LOAD] - df[COL_FORECAST_LOAD]
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["Forecast Error"],
        fill="tozeroy", mode="lines", name="Error",
        line=dict(color=ADALAN_COLORS[1]),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=ADALAN_COLORS[5])
    fig.update_layout(title="Forecast Error (MW)", template="adalan",
                      xaxis_title="", yaxis_title="MW")
    st.plotly_chart(fig, use_container_width=True)

    # Average daily profile by hour
    df["Hour"] = df.index.hour
    hourly = df.groupby("Hour")[COL_ACTUAL_LOAD].mean().reset_index()
    fig = go.Figure(go.Scatter(
        x=hourly["Hour"], y=hourly[COL_ACTUAL_LOAD],
        mode="lines+markers", line=dict(color=ADALAN_COLORS[0]),
    ))
    fig.update_layout(title="Average Daily Load Profile by Hour", template="adalan",
                      xaxis_title="Hour of Day", yaxis_title="Avg MW")
    st.plotly_chart(fig, use_container_width=True)

    # Statistics + histogram
    stats = df[COL_ACTUAL_LOAD].describe()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statistics")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Min", f"{stats['min']:,.0f} MW")
        s2.metric("Max", f"{stats['max']:,.0f} MW")
        s3.metric("Mean", f"{stats['mean']:,.0f} MW")
        s4.metric("Std Dev", f"{stats['std']:,.0f} MW")
    with col2:
        fig = go.Figure(go.Histogram(
            x=df[COL_ACTUAL_LOAD], marker_color=ADALAN_COLORS[0], name="Load",
        ))
        fig.update_layout(title="Load Distribution", template="adalan",
                          xaxis_title="MW", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    # Daily summary table
    df["Date"] = df.index.date
    daily = df.groupby("Date").agg(
        actual_gwh=(COL_ACTUAL_LOAD, lambda x: _to_gwh(x.sum())),
        forecast_gwh=(COL_FORECAST_LOAD, lambda x: _to_gwh(x.sum())),
    ).reset_index()
    daily["error_gwh"] = daily["actual_gwh"] - daily["forecast_gwh"]
    daily.columns = ["Date", "Actual (GWh)", "Forecast (GWh)", "Error (GWh)"]
    daily = daily.round(2)
    st.subheader("Daily Summary")
    st.dataframe(daily, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 3 — Generation Details
# ---------------------------------------------------------------------------

def _render_generation_details(gen_df: pd.DataFrame) -> None:
    if gen_df.empty:
        st.warning("No generation data available.")
        return

    cmap = _color_map(gen_df.columns)
    idx_name = gen_df.index.name or "timestamp"

    # Stacked area
    df_m = gen_df.reset_index().melt(id_vars=idx_name, var_name="Source", value_name="MW")
    fig = go.Figure()
    for src in gen_df.columns:
        src_data = df_m[df_m["Source"] == src]
        fig.add_trace(go.Scatter(
            x=src_data[idx_name], y=src_data["MW"],
            name=src, stackgroup="one", mode="lines",
            line=dict(width=0), fillcolor=cmap.get(src, ADALAN_COLORS[0]),
        ))
    fig.update_layout(title="Generation by Technology (MW)", template="adalan",
                      xaxis_title="", yaxis_title="MW")
    st.plotly_chart(fig, use_container_width=True)

    # Donut + horizontal bar
    avg_mw = gen_df.mean().sort_values(ascending=False)
    colors_list = [cmap.get(s, ADALAN_COLORS[0]) for s in avg_mw.index]

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Pie(
            labels=avg_mw.index, values=avg_mw.values, hole=0.4,
            marker=dict(colors=colors_list),
        ))
        fig.update_layout(title="Average Generation Mix", template="adalan")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        avg_sorted = avg_mw.sort_values(ascending=True)
        fig = go.Figure(go.Bar(
            x=avg_sorted.values, y=avg_sorted.index, orientation="h",
            marker_color=[cmap.get(s, ADALAN_COLORS[0]) for s in avg_sorted.index],
        ))
        fig.update_layout(title="Average MW per Technology", template="adalan",
                          xaxis_title="MW", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # KPIs
    total_gwh = _to_gwh(gen_df.sum().sum())
    nuc_cols = [c for c in gen_df.columns if c in NUCLEAR_TYPES]
    ren_cols = [c for c in gen_df.columns if c in RENEWABLE_TYPES]
    nuc_sum = gen_df[nuc_cols].sum().sum() if nuc_cols else 0.0
    ren_sum = gen_df[ren_cols].sum().sum() if ren_cols else 0.0
    total_sum = gen_df.sum().sum()

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Generation", f"{total_gwh:,.1f} GWh")
    k2.metric("Nuclear Share", f"{_safe_pct(nuc_sum, total_sum):.1f} %")
    k3.metric("Renewable Share", f"{_safe_pct(ren_sum, total_sum):.1f} %")

    # Daily generation summary table
    df = gen_df.copy()
    df["Date"] = df.index.date
    daily = df.groupby("Date")[list(gen_df.columns)].sum() * MW_TO_GWH
    daily.index.name = "Date"
    st.subheader("Daily Generation Summary (GWh)")
    st.dataframe(daily.round(2), use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 4 — Installed Capacity
# ---------------------------------------------------------------------------

def _render_installed_capacity(cap_df: pd.DataFrame, gen_df: pd.DataFrame) -> None:
    if cap_df.empty:
        st.warning("No installed capacity data available.")
        return

    latest = cap_df.iloc[-1].dropna()
    latest = latest[latest > 0].sort_values(ascending=False)
    cmap = _color_map(latest.index)

    # Horizontal bar + donut
    col1, col2 = st.columns(2)
    with col1:
        lat_asc = latest.sort_values(ascending=True)
        fig = go.Figure(go.Bar(
            x=lat_asc.values, y=lat_asc.index, orientation="h",
            marker_color=[cmap.get(s, ADALAN_COLORS[0]) for s in lat_asc.index],
        ))
        fig.update_layout(title="Installed Capacity by Technology (MW)", template="adalan",
                          xaxis_title="MW", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = go.Figure(go.Pie(
            labels=latest.index, values=latest.values, hole=0.4,
            marker=dict(colors=[cmap.get(s, ADALAN_COLORS[0]) for s in latest.index]),
        ))
        fig.update_layout(title="Capacity Share", template="adalan")
        st.plotly_chart(fig, use_container_width=True)

    # Capacity vs average generation side-by-side
    if not gen_df.empty:
        avg_gen = gen_df.mean()
        common = latest.index.intersection(avg_gen.index)
        if len(common) > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Installed Capacity (MW)", x=list(common), y=latest[common].values,
                marker_color=ADALAN_COLORS[0],
            ))
            fig.add_trace(go.Bar(
                name="Avg Generation (MW)", x=list(common), y=avg_gen[common].values,
                marker_color=ADALAN_COLORS[2],
            ))
            fig.update_layout(barmode="group", title="Capacity vs Average Generation",
                               template="adalan", xaxis_title="", yaxis_title="MW")
            st.plotly_chart(fig, use_container_width=True)

    # KPIs
    total_gw = latest.sum() / 1000
    top3 = ", ".join(latest.head(3).index.tolist())
    k1, k2 = st.columns(2)
    k1.metric("Total Installed Capacity", f"{total_gw:.1f} GW")
    k2.info(f"Top 3 technologies: {top3}")

    # Capacity factor table
    if not gen_df.empty:
        avg_gen = gen_df.mean()
        common = latest.index.intersection(avg_gen.index)
        if len(common) > 0:
            rows = []
            for tech in common:
                cap = latest[tech]
                avg = avg_gen[tech]
                rows.append({
                    "Technology": tech,
                    "Capacity (MW)": round(cap, 0),
                    "Avg Generation (MW)": round(avg, 1),
                    "Capacity Factor (%)": round(_safe_pct(avg, cap), 1),
                })
            st.subheader("Capacity Factor per Technology")
            st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 5 — Wind & Solar Details
# ---------------------------------------------------------------------------

def _render_wind_solar(
    wsf_df: pd.DataFrame,
    gen_df: pd.DataFrame,
    cap_df: pd.DataFrame,
) -> None:
    sources = ["Solar", "Wind Onshore", "Wind Offshore"]

    if wsf_df.empty and gen_df.empty:
        st.warning("No wind/solar data available.")
        return

    # Per-source forecast vs actual
    for src in sources:
        fcast_col = next((c for c in wsf_df.columns if src in c), None)
        actual_col = src if src in gen_df.columns else None
        if not fcast_col and not actual_col:
            continue

        st.subheader(src)
        fig = go.Figure()
        if actual_col:
            fig.add_trace(go.Scatter(
                x=gen_df.index, y=gen_df[actual_col],
                mode="lines", name="Actual", line=dict(color=ADALAN_COLORS[0]),
            ))
        if fcast_col:
            fig.add_trace(go.Scatter(
                x=wsf_df.index, y=wsf_df[fcast_col],
                mode="lines", name="Forecast", line=dict(color=ADALAN_COLORS[1], dash="dash"),
            ))
        fig.update_layout(title=f"{src}: Forecast vs Actual (MW)", template="adalan",
                          xaxis_title="", yaxis_title="MW")
        st.plotly_chart(fig, use_container_width=True)

    # Forecast error with zero line
    fcast_cols = [c for c in wsf_df.columns if any(s in c for s in sources)]
    actual_ren_cols = [c for c in gen_df.columns if c in sources]
    if fcast_cols and actual_ren_cols:
        total_fcast = wsf_df[fcast_cols].sum(axis=1)
        total_actual = gen_df[actual_ren_cols].sum(axis=1)
        error = (total_actual - total_fcast).dropna()
        fig = go.Figure(go.Scatter(
            x=error.index, y=error.values,
            fill="tozeroy", mode="lines", name="Error",
            line=dict(color=ADALAN_COLORS[4]),
        ))
        fig.add_hline(y=0, line_dash="dash", line_color=ADALAN_COLORS[5])
        fig.update_layout(title="Total Renewable Forecast Error (MW)", template="adalan",
                          xaxis_title="", yaxis_title="MW")
        st.plotly_chart(fig, use_container_width=True)

    # Hourly daily profile
    if not gen_df.empty and actual_ren_cols:
        df = gen_df[actual_ren_cols].copy()
        df["Hour"] = df.index.hour
        profile = df.groupby("Hour")[actual_ren_cols].mean()
        fig = go.Figure()
        for i, src in enumerate(actual_ren_cols):
            fig.add_trace(go.Scatter(
                x=profile.index, y=profile[src],
                mode="lines+markers", name=src,
                line=dict(color=ADALAN_COLORS[i % len(ADALAN_COLORS)]),
            ))
        fig.update_layout(title="Average Daily Profile by Hour (MW)", template="adalan",
                          xaxis_title="Hour of Day", yaxis_title="Avg MW")
        st.plotly_chart(fig, use_container_width=True)

    # KPIs with capacity factors
    if not gen_df.empty and not cap_df.empty:
        latest_cap = cap_df.iloc[-1]
        kpi_sources = [s for s in sources if s in gen_df.columns]
        if kpi_sources:
            k_cols = st.columns(len(kpi_sources))
            for i, src in enumerate(kpi_sources):
                avg_gen = gen_df[src].mean()
                cap = latest_cap.get(src, 0)
                cf = _safe_pct(avg_gen, cap) if cap else 0.0
                k_cols[i].metric(f"{src} Avg", f"{avg_gen:,.0f} MW")
                k_cols[i].caption(f"Capacity Factor: {cf:.1f} %")

    # Daily GWh pivot table
    if not gen_df.empty and actual_ren_cols:
        df = gen_df[actual_ren_cols].copy()
        df["Date"] = df.index.date
        pivot = df.groupby("Date")[actual_ren_cols].sum() * MW_TO_GWH
        st.subheader("Daily Generation (GWh)")
        st.dataframe(pivot.round(2), use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 6 — Cross-Border Details
# ---------------------------------------------------------------------------

def _render_crossborder(cb_dict: dict[str, pd.DataFrame]) -> None:
    if not cb_dict:
        st.warning("No cross-border data available.")
        return

    nb_keys = [nb for nb in cb_dict if COL_NET_IMPORT in cb_dict[nb].columns]

    # Net imports total line chart
    if nb_keys:
        net_all = pd.DataFrame({nb: cb_dict[nb][COL_NET_IMPORT] for nb in nb_keys})
        net_total = net_all.sum(axis=1)
        fig = go.Figure(go.Scatter(
            x=net_total.index, y=net_total.values,
            mode="lines", name="Total Net Import", line=dict(color=ADALAN_COLORS[0]),
        ))
        fig.add_hline(y=0, line_dash="dash", line_color=ADALAN_COLORS[5])
        fig.update_layout(title="Total Net Imports (MW, positive = import)",
                          template="adalan", xaxis_title="", yaxis_title="MW")
        st.plotly_chart(fig, use_container_width=True)

    # Per-neighbour 3×2 grid
    neighbours = list(cb_dict.keys())
    for i in range(0, len(neighbours), 2):
        cols = st.columns(2)
        for j, nb in enumerate(neighbours[i:i + 2]):
            df = cb_dict[nb]
            with cols[j]:
                fig = go.Figure()
                if COL_IMPORT in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df[COL_IMPORT],
                                             mode="lines", name="Import",
                                             line=dict(color=ADALAN_COLORS[3])))
                if COL_EXPORT in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df[COL_EXPORT],
                                             mode="lines", name="Export",
                                             line=dict(color=ADALAN_COLORS[5])))
                if COL_NET_IMPORT in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df[COL_NET_IMPORT],
                                             mode="lines", name="Net Import",
                                             line=dict(color=ADALAN_COLORS[0], dash="dash")))
                fig.update_layout(title=f"France ↔ {nb} (MW)", template="adalan",
                                   xaxis_title="", yaxis_title="MW")
                st.plotly_chart(fig, use_container_width=True)

    # Daily net import stacked bar
    if nb_keys:
        net_all_copy = net_all.copy()
        net_all_copy["Date"] = net_all_copy.index.date
        daily_net = net_all_copy.groupby("Date")[nb_keys].sum() * MW_TO_GWH
        daily_net_m = daily_net.reset_index().melt(id_vars="Date", var_name="Neighbour", value_name="GWh")
        fig = go.Figure()
        for i, nb in enumerate(nb_keys):
            nb_data = daily_net_m[daily_net_m["Neighbour"] == nb]
            fig.add_trace(go.Bar(
                x=nb_data["Date"], y=nb_data["GWh"], name=nb,
                marker_color=ADALAN_COLORS[i % len(ADALAN_COLORS)],
            ))
        fig.update_layout(barmode="relative",
                          title="Daily Net Import by Neighbour (GWh, positive = import)",
                          template="adalan", xaxis_title="", yaxis_title="GWh")
        st.plotly_chart(fig, use_container_width=True)

    # Total energy exchanged grouped bar
    total_stats = []
    for nb, df in cb_dict.items():
        total_import = _to_gwh(df[COL_IMPORT].sum()) if COL_IMPORT in df.columns else 0.0
        total_export = _to_gwh(df[COL_EXPORT].sum()) if COL_EXPORT in df.columns else 0.0
        total_stats.append({"Neighbour": nb, "Import (GWh)": total_import, "Export (GWh)": total_export})
    if total_stats:
        stats_df = pd.DataFrame(total_stats)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Import (GWh)", x=stats_df["Neighbour"], y=stats_df["Import (GWh)"],
                             marker_color=ADALAN_COLORS[3]))
        fig.add_trace(go.Bar(name="Export (GWh)", x=stats_df["Neighbour"], y=stats_df["Export (GWh)"],
                             marker_color=ADALAN_COLORS[5]))
        fig.update_layout(barmode="group", title="Total Energy Exchanged per Neighbour (GWh)",
                          template="adalan", xaxis_title="", yaxis_title="GWh")
        st.plotly_chart(fig, use_container_width=True)

    # KPIs
    if nb_keys:
        total_net = {nb: _to_gwh(net_all[nb].sum()) for nb in nb_keys}
        total_net_gwh = sum(total_net.values())
        largest_importer = max(total_net, key=total_net.get)
        largest_exporter = min(total_net, key=total_net.get)
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Net GWh", f"{total_net_gwh:,.1f} GWh")
        k2.metric("Largest Importer", largest_importer)
        k3.metric("Largest Exporter", largest_exporter)

    # Daily net import summary table
    if nb_keys:
        daily_summary = net_all.copy()
        daily_summary["Date"] = daily_summary.index.date
        daily_table = daily_summary.groupby("Date")[nb_keys].sum() * MW_TO_GWH
        daily_table.index.name = "Date"
        st.subheader("Daily Net Import Summary (GWh)")
        st.dataframe(daily_table.round(2), use_container_width=True)


# ---------------------------------------------------------------------------
# Page layout & rendering
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Entsoe-AI-Warriors", page_icon="⚡", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1A3A5C; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div.stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }
.stApp { background-color: #F4F7FB; }
</style>
""", unsafe_allow_html=True)

# Initial data collection (US-044)
if not (PROCESSED_DIR / "prices.csv").exists():
    with st.spinner("Collecting initial data, please wait..."):
        try:
            collect_data()
            process_data()
            with _refresh_lock:
                _last_data_update = pd.Timestamp.now()
        except Exception as _exc:
            st.error(
                f"Initial data collection failed: {_exc}\n\n"
                "Please ensure ENTSOE_API_KEY is set in your .env file and try again."
            )
            st.stop()

_ensure_refresh_thread()

# Sidebar
with st.sidebar:
    st.title("⚡ Entsoe-AI-Warriors")
    st.markdown("---")

    _today = pd.Timestamp.now().date()
    _week_ago = (pd.Timestamp.now() - pd.Timedelta(days=7)).date()
    start_date = st.date_input("Start date", value=_week_ago)
    end_date = st.date_input("End date", value=_today)

    st.markdown("---")
    with _refresh_lock:
        _ts = _last_data_update
        _err = _refresh_last_error
        _prog = _refresh_in_progress

    if _ts is not None:
        st.caption(f"Last download: {_ts.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.caption("No automatic refresh yet")

    if _prog:
        st.info("Refreshing data...")

    if _err:
        st.warning(f"Last refresh failed:\n{_err}")

# Date range as timestamps
_start_ts = pd.Timestamp(start_date)
_end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)

# Load and filter data
try:
    _prices = filter_by_date(load_prices(), _start_ts, _end_ts)
except Exception as _e:
    st.error(f"Failed to load prices: {_e}")
    _prices = pd.DataFrame()

try:
    _load = filter_by_date(load_load(), _start_ts, _end_ts)
except Exception as _e:
    st.error(f"Failed to load load data: {_e}")
    _load = pd.DataFrame()

try:
    _gen = filter_by_date(load_generation(), _start_ts, _end_ts)
except Exception as _e:
    st.error(f"Failed to load generation: {_e}")
    _gen = pd.DataFrame()

try:
    _wsf = filter_by_date(load_wind_solar_forecast(), _start_ts, _end_ts)
except Exception as _e:
    st.error(f"Failed to load wind/solar forecast: {_e}")
    _wsf = pd.DataFrame()

try:
    _cap = load_installed_capacity()
except Exception as _e:
    st.error(f"Failed to load installed capacity: {_e}")
    _cap = pd.DataFrame()

try:
    _cb_raw = load_crossborder()
    _cb = {nb: filter_by_date(df, _start_ts, _end_ts) for nb, df in _cb_raw.items()}
except Exception as _e:
    st.error(f"Failed to load cross-border data: {_e}")
    _cb = {}

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⚡ Overview",
    "🔌 Load Details",
    "🏭 Generation Details",
    "🔋 Installed Capacity",
    "🌿 Wind & Solar Details",
    "🔀 Cross-Border Details",
])

with tab1:
    _render_overview(_prices, _load, _gen, _wsf, _cap, _cb)

with tab2:
    _render_load_details(_load)

with tab3:
    _render_generation_details(_gen)

with tab4:
    _render_installed_capacity(_cap, _gen)

with tab5:
    _render_wind_solar(_wsf, _gen, _cap)

with tab6:
    _render_crossborder(_cb)

# Poll for new data every POLL_INTERVAL_SECONDS
time.sleep(POLL_INTERVAL_SECONDS)
st.rerun()
