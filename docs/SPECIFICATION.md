# Entsoe-AI-Warriors — Product Specification

**Version:** 1.0
**Date:** 2026-04-09
**Branch:** dev-bmad

---

## 1. Purpose

Entsoe-AI-Warriors is a Python application that collects real-time and historical electricity data for France from the ENTSO-E Transparency Platform, transforms it into clean analysis-ready datasets, and renders an interactive web dashboard.

---

## 2. High-Level Architecture

The system is a three-stage pipeline:

```
[ENTSO-E API] → collect_france.py → data/ (raw CSVs)
                                         ↓
                              process_france.py → data/processed/ (clean CSVs)
                                                         ↓
                                              dashboard.py → Streamlit web UI
```

The dashboard embeds a background thread that re-runs the collect → process pipeline automatically every 15 minutes.

---

## 3. Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Package manager | `uv` |
| Build system | Hatch (`pyproject.toml`) |
| API client | `entsoe-py >= 0.7` |
| Data manipulation | `pandas` |
| Web framework | `streamlit >= 1.30` |
| Charts | `plotly >= 6.0` |
| Environment | `python-dotenv >= 1.0` |
| Dev tools | `pytest`, `ruff`, `mypy` |

**Configuration:** `ENTSOE_API_KEY` must be set in a `.env` file at the project root.

---

## 4. Module Specifications

### 4.1 `client.py` — API Client Factory

**Responsibility:** Single source of truth for creating an authenticated ENTSO-E API client.

**Public interface:**

```python
def get_client() -> EntsoePandasClient
```

- Loads `.env` via `python-dotenv`
- Reads `ENTSOE_API_KEY` from environment
- Raises `RuntimeError` if the key is missing
- Returns a configured `EntsoePandasClient` instance

---

### 4.2 `collect_france.py` — Data Collection

**Responsibility:** Fetch raw energy data from ENTSO-E API and save as CSV files in `data/`.

**Country code:** `FR` (France)
**Default period:** Last 7 days (computed at runtime relative to current UTC time, converted to `Europe/Paris`)

**Data collected:**

| Dataset | ENTSO-E query | Output file |
|---------|--------------|-------------|
| Day-ahead prices | `query_day_ahead_prices` | `data/france_day_ahead_prices.csv` |
| Load actual + forecast | `query_load_and_forecast` | `data/france_load.csv` |
| Generation by type | `query_generation` (all PSR types) | `data/france_generation_by_type.csv` |
| Wind & solar forecast | `query_wind_and_solar_forecast` | `data/france_wind_solar_forecast.csv` |
| Installed capacity | `query_installed_generation_capacity` | `data/france_installed_capacity.csv` |
| Cross-border flows | `query_crossborder_flows` (per neighbour, both directions) | `data/france_crossborder_{direction}.csv` |

**Cross-border neighbours:**

| Key | EIC Code |
|-----|---------|
| BE (Belgium) | 10YBE----------2 |
| DE_LU (Germany/Luxembourg) | 10Y1001A1001A82H |
| ES (Spain) | 10YES-REE------0 |
| GB (Great Britain) | 10YGB----------A |
| IT_NORD (Italy North) | 10Y1001A1001A73I |
| CH (Switzerland) | 10YCH-SWISSGRIDZ |

France EIC: `10YFR-RTE------C`

Cross-border files follow the pattern:
- `france_crossborder_FR_to_{NEIGHBOUR}.csv` — exports
- `france_crossborder_{NEIGHBOUR}_to_FR.csv` — imports

**Error handling:** Each collection step is independent. A failure in one step is logged as an exception but does not prevent other steps from running. Per-neighbour cross-border failures are also handled individually.

**Entry point:** `main()` — callable as `python -m entsoe_ai_warriors.collect_france`

---

### 4.3 `process_france.py` — Data Processing

**Responsibility:** Read raw CSVs from `data/`, clean and transform them, write analysis-ready CSVs to `data/processed/`.

**Exported constants (imported by `dashboard.py`):**

| Constant | Value |
|----------|-------|
| `PROCESSED_DIR` | `data/processed/` (as `pathlib.Path`) |
| `COL_PRICE` | `"Price"` |
| `COL_ACTUAL_LOAD` | `"Actual Load"` |
| `COL_FORECAST_LOAD` | `"Forecasted Load"` |
| `COL_IMPORT` | `"Import"` |
| `COL_EXPORT` | `"Export"` |
| `COL_NET_IMPORT` | `"Net Import"` |

**Processing rules per dataset:**

**Prices (`prices.csv`):**
- Read with single-level header, parse dates as index
- Rename single column to `COL_PRICE`
- Raise `ValueError` if empty

**Load (`load.csv`):**
- Read with standard header, parse dates as index
- Validate that both `COL_ACTUAL_LOAD` and `COL_FORECAST_LOAD` columns exist
- Raise `ValueError` if empty or columns missing

**Generation (`generation.csv`):**
- Read with two-level header (multi-index: technology + sub-category), parse dates as index
- Filter to columns where sub-level == `"Actual Aggregated"`
- Flatten to single-level header using technology names only
- Raise `ValueError` if no aggregated columns found or result is empty

**Wind & Solar Forecast (`wind_solar_forecast.csv`):**
- Read as-is, parse dates as index

**Installed Capacity (`installed_capacity.csv`):**
- Read as-is, parse dates as index

**Cross-border flows (`crossborder_{NEIGHBOUR}.csv` for each neighbour):**
- Read both `FR_to_{nb}` (export) and `{nb}_to_FR` (import) files
- Rename to `COL_EXPORT` and `COL_IMPORT` respectively
- Outer-join on timestamp index
- Compute `COL_NET_IMPORT = COL_IMPORT - COL_EXPORT`
- Save one file per neighbour: `crossborder_{nb}.csv`

**Error handling:** Same independent-step pattern as collect — failures are logged, other steps proceed.

**Entry point:** `main()` — callable as `python -m entsoe_ai_warriors.process_france`

---

### 4.4 `dashboard.py` — Streamlit Web Dashboard

**Responsibility:** Load processed CSVs, filter by user-selected date range, render all charts and KPIs. No data transformation — read-only consumer of `data/processed/`.

#### 4.4.1 Visual Theme

**Plotly template name:** `adalan` (registered globally via `pio.templates`)

| Token | Value |
|-------|-------|
| Primary blue | `#2299DD` |
| Orange accent | `#F57C00` |
| Teal | `#00ACC1` |
| Green | `#43A047` |
| Purple | `#8E24AA` |
| Red | `#E53935` |
| Amber | `#FB8C00` |
| Indigo | `#3949AB` |
| Font | `'Inter', 'Segoe UI', Arial, sans-serif` |
| Text color | `#1A2940` |
| Paper background | `#FFFFFF` |
| Plot background | `#F4F7FB` |
| Grid color | `rgba(34,153,221,0.12)` |

**Sidebar background:** `#1A3A5C` (dark navy), all text `#FFFFFF`
**App background:** `#F4F7FB`

**Per-source color overrides (`SOURCE_COLORS`):**

| Source | Color |
|--------|-------|
| Solar | `#F57C00` |
| Hydro Pumped Storage | `#2299DD` |
| Hydro Run-of-river and poundage | `#00ACC1` |
| Hydro Water Reservoir | `#3949AB` |

#### 4.4.2 Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `REFRESH_INTERVAL_SECONDS` | `900` (15 min) | Background refresh period |
| `POLL_INTERVAL_SECONDS` | `30` | How often UI checks for new data |
| `INTERVAL_HOURS` | `0.25` | 15-minute interval in hours |
| `MW_TO_GWH` | `0.25 / 1000 = 0.00025` | MW sum → GWh conversion factor |

**Renewable types:** Solar, Wind Offshore, Wind Onshore, Hydro Run-of-river and poundage, Hydro Water Reservoir
**Nuclear types:** Nuclear

#### 4.4.3 Background Refresh

- A daemon thread (`_refresh_loop`) runs `collect_data()` then `process_data()` in a loop, sleeping `REFRESH_INTERVAL_SECONDS` between runs
- Thread is started once per process via `_ensure_refresh_thread()`, guarded by `st.session_state.refresh_thread_started`
- On success: updates `_last_data_update` timestamp and calls `st.cache_data.clear()`
- On failure: stores error string in `_refresh_last_error`
- Thread-safety: `_refresh_lock` protects shared state variables

#### 4.4.4 Data Loaders

All loaders are decorated with `@st.cache_data`:

| Function | File read |
|----------|-----------|
| `load_prices()` | `prices.csv` |
| `load_load()` | `load.csv` |
| `load_generation()` | `generation.csv` |
| `load_wind_solar_forecast()` | `wind_solar_forecast.csv` |
| `load_installed_capacity()` | `installed_capacity.csv` |
| `load_crossborder()` | `crossborder_{nb}.csv` for all neighbours → returns `dict[str, DataFrame]` |

#### 4.4.5 Sidebar

- Date range picker: `start_date` / `end_date` (defaults: last 7 days)
- Last refresh timestamp (from `_last_data_update`)
- Warning banner if `_refresh_last_error` is set

#### 4.4.6 Dashboard Tabs

**Tab 1 — ⚡ Overview**
- KPIs: average price (€/MWh), peak load (MW), total generation (GWh), renewable share (%)
- Day-ahead prices line chart
- Load actual vs forecast line chart
- Generation mix stacked area chart
- Generation mix donut chart
- Renewables forecast vs actual line chart
- Installed capacity horizontal bar chart
- Cross-border net flows chart

**Tab 2 — 🔌 Load Details**
- Large actual vs forecast line chart
- Forecast error line chart (filled to zero)
- Average daily profile by hour (line chart, grouped by hour of day)
- Statistics panel: min, max, mean, std
- Load histogram
- Daily summary table (date, actual GWh, forecast GWh, error GWh)

**Tab 3 — 🏭 Generation Details**
- Stacked area chart by technology
- Donut chart (average MW per source)
- Horizontal bar chart (average MW per source)
- KPIs: total GWh, nuclear share (%), renewable share (%)
- Daily generation summary table (date × technology)

**Tab 4 — 🔋 Installed Capacity**
- Horizontal bar chart (capacity by technology)
- Donut chart (capacity share)
- Side-by-side bar: capacity vs average generation per technology
- KPIs: total GW, top 3 technologies
- Capacity factor table per technology

**Tab 5 — 🌿 Wind & Solar Details**
- Per-source forecast vs actual charts: Solar, Wind Onshore, Wind Offshore
- Forecast error chart with zero line
- Hourly daily profile chart
- KPIs with capacity factors per source
- Daily GWh pivot table

**Tab 6 — 🔀 Cross-Border Details**
- Net imports total line chart
- Per-neighbour 3×2 grid: import / export / net (6 neighbours)
- Daily net import stacked bar chart
- Total energy exchanged grouped bar chart
- KPIs: total net GWh, largest importer, largest exporter
- Daily net import summary table

#### 4.4.7 Helper Functions

```python
def _safe_pct(numerator: float, denominator: float) -> float
    # Returns numerator/denominator*100, or 0.0 if denominator is 0 or NaN

def _to_gwh(mw_sum: float) -> float
    # Returns mw_sum * MW_TO_GWH

def filter_by_date(df: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame
    # Returns rows where index >= start and index < end
```

---

## 5. Data Flow Summary

```
ENTSO-E API
    │
    ▼ (collect_france.py)
data/
    france_day_ahead_prices.csv        — Series: timestamp → price (€/MWh)
    france_load.csv                    — DataFrame: timestamp × [Actual Load, Forecasted Load]
    france_generation_by_type.csv      — DataFrame: timestamp × [tech, sub-type] (multi-header)
    france_wind_solar_forecast.csv     — DataFrame: timestamp × [Solar, Wind Onshore, Wind Offshore]
    france_installed_capacity.csv      — DataFrame: timestamp × technologies
    france_crossborder_FR_to_{nb}.csv  — Series per neighbour: timestamp → MW export
    france_crossborder_{nb}_to_FR.csv  — Series per neighbour: timestamp → MW import
    │
    ▼ (process_france.py)
data/processed/
    prices.csv                — timestamp × [Price]
    load.csv                  — timestamp × [Actual Load, Forecasted Load]
    generation.csv            — timestamp × [technology...] (single-level, Actual Aggregated only)
    wind_solar_forecast.csv   — timestamp × [Solar, Wind Onshore, Wind Offshore, ...]
    installed_capacity.csv    — timestamp × [technology...]
    crossborder_{nb}.csv      — timestamp × [Import, Export, Net Import]  (per neighbour)
    │
    ▼ (dashboard.py)
Streamlit web UI — read-only, filtered by date range selector
```

---

## 6. File & Directory Structure

```
Entsoe-AI-Warriors/
├── src/
│   └── entsoe_ai_warriors/
│       ├── client.py               # API client factory
│       ├── collect_france.py       # Stage 1: collect
│       ├── process_france.py       # Stage 2: process
│       └── dashboard.py            # Stage 3: render
├── data/
│   ├── *.csv                       # Raw files (gitignored)
│   └── processed/
│       └── *.csv                   # Clean files (gitignored)
├── .env                            # ENTSOE_API_KEY (not committed)
├── pyproject.toml                  # Hatch build + dependencies
└── docs/
    └── SPECIFICATION.md            # This file
```

---

## 7. Entry Points & Commands

| Command | Action |
|---------|--------|
| `uv sync` | Install runtime dependencies |
| `uv sync --extra dev` | Install with dev tools (pytest, ruff, mypy) |
| `uv run streamlit run src/entsoe_ai_warriors/dashboard.py` | Launch dashboard |
| `uv run python -m entsoe_ai_warriors.collect_france` | Collect raw data |
| `uv run python -m entsoe_ai_warriors.process_france` | Process raw → clean |

---

## 8. Constraints & Non-Goals

- Data scope: France only (`FR` / `10YFR-RTE------C`)
- No database — all storage is flat CSV files
- No authentication on the dashboard — single-user local tool
- No historical backfill — always fetches last 7 days
- No unit tests currently exist for `collect_france.py` or `dashboard.py`
- The dashboard does **not** transform data; all transformations happen in `process_france.py`
