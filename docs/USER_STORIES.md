# User Stories — Entsoe-AI-Warriors

**Version:** 1.0
**Date:** 2026-04-09
**Status:** Baseline (reflects existing implemented features)

Stories are tagged with their implementation status:
- `[DONE]` — already implemented
- `[TODO]` — not yet implemented

---

## Epic 1 — Data Collection

**Goal:** Fetch fresh energy data from ENTSO-E API reliably.

---

**US-001** `[DONE]`
> As an **operator**, I want to collect day-ahead electricity prices for France, so that the dashboard can display market price trends.

**Acceptance criteria:**
- Data covers the last 7 days
- Output saved as `data/france_day_ahead_prices.csv`
- A failure does not block other collection steps

---

**US-002** `[DONE]`
> As an **operator**, I want to collect actual and forecast load for France, so that the dashboard can compare what was predicted vs what actually happened.

**Acceptance criteria:**
- Both "Actual Load" and "Forecasted Load" columns are present
- Output saved as `data/france_load.csv`
- A failure does not block other collection steps

---

**US-003** `[DONE]`
> As an **operator**, I want to collect actual generation per technology type for France, so that the dashboard can show the energy mix.

**Acceptance criteria:**
- All PSR types (Nuclear, Solar, Wind, Hydro, etc.) are fetched
- Output saved as `data/france_generation_by_type.csv`
- A failure does not block other collection steps

---

**US-004** `[DONE]`
> As an **operator**, I want to collect wind and solar forecasts for France, so that the dashboard can compare renewable forecast vs actual generation.

**Acceptance criteria:**
- Solar, Wind Onshore, Wind Offshore forecasts included
- Output saved as `data/france_wind_solar_forecast.csv`
- A failure does not block other collection steps

---

**US-005** `[DONE]`
> As an **operator**, I want to collect installed generation capacity for France, so that the dashboard can compute capacity factors.

**Acceptance criteria:**
- All technology types included
- Output saved as `data/france_installed_capacity.csv`
- A failure does not block other collection steps

---

**US-006** `[DONE]`
> As an **operator**, I want to collect cross-border physical flows between France and all its neighbours (BE, CH, DE_LU, ES, GB, IT_NORD) in both directions, so that the dashboard can show net import/export per country.

**Acceptance criteria:**
- Both directions collected per neighbour (FR→X and X→FR)
- Per-neighbour failures are skipped gracefully without stopping the rest
- Output saved as `data/france_crossborder_FR_to_{nb}.csv` and `data/france_crossborder_{nb}_to_FR.csv`

---

## Epic 2 — Data Processing

**Goal:** Transform raw API data into clean, analysis-ready CSVs.

---

**US-007** `[DONE]`
> As a **developer**, I want raw CSVs to be cleaned and normalised into a consistent format, so that the dashboard can load data without performing transformations.

**Acceptance criteria:**
- All processed files have a `timestamp` index
- Column names match `COL_*` constants defined in `process_france.py`
- A failure in one dataset does not prevent others from being processed

---

**US-008** `[DONE]`
> As a **developer**, I want generation data to be flattened from multi-level headers to a single-level header (Actual Aggregated values only), so that the dashboard can iterate over technology columns directly.

**Acceptance criteria:**
- Output has one column per technology type
- Only `"Actual Aggregated"` sub-rows are kept
- Error raised if no aggregated columns are found

---

**US-009** `[DONE]`
> As a **developer**, I want cross-border flow files to include Import, Export, and Net Import columns, so that the dashboard can display net flows without computing them.

**Acceptance criteria:**
- `Net Import = Import - Export`
- Outer join on timestamp (no data lost if one direction has gaps)
- One file per neighbour: `data/processed/crossborder_{nb}.csv`

---

## Epic 3 — Dashboard — General

**Goal:** A web dashboard that lets users explore French electricity data interactively.

---

**US-010** `[DONE]`
> As a **user**, I want to filter all charts by a date range, so that I can focus on a specific period of interest.

**Acceptance criteria:**
- Date range selector in the sidebar
- Default range: last 7 days
- All charts update when the date range changes

---

**US-011** `[DONE]`
> As a **user**, I want the dashboard data to refresh automatically every 15 minutes, so that I always see up-to-date information without restarting the app.

**Acceptance criteria:**
- Background thread runs collect → process every 15 minutes
- Sidebar shows the timestamp of the last successful refresh
- Sidebar shows a warning if the last refresh failed
- On refresh, Streamlit cache is cleared so charts reload

---

**US-043** `[DONE]`
> As a **user**, I want to see the refresh status in the sidebar (last update timestamp, in-progress indicator, and error warning), so that I know whether the data is current and whether the last refresh succeeded.

**Acceptance criteria:**
- Sidebar shows timestamp of last successful data download (set by both the initial collection and background refresh)
- Sidebar shows an in-progress indicator while refresh is running
- Sidebar shows a visible warning banner if the last refresh failed, including the error message
- Status updates automatically without requiring a page reload

---

**US-044** `[DONE]`
> As a **first-time user**, I want the dashboard to automatically collect initial data if no processed data exists yet, so that I do not need to run the collection script manually before opening the dashboard.

**Acceptance criteria:**
- On startup, if `data/processed/prices.csv` is missing, the dashboard triggers `collect_france.main()` then `process_france.main()` automatically
- The UI displays a clear "Collecting initial data..." message while this runs
- If collection fails, the dashboard shows an actionable error message (not a crash)
- Once data is available, the dashboard renders normally without a restart

---

## Epic 4 — Dashboard — Overview Tab

**Goal:** A single-screen summary of the current energy situation in France.

---

**US-012** `[DONE]`
> As a **user**, I want to see key performance indicators (average price, peak load, total generation, renewable share) at a glance, so that I can quickly assess the energy situation.

---

**US-013** `[DONE]`
> As a **user**, I want to see a day-ahead price chart, so that I can track electricity market prices over time.

---

**US-014** `[DONE]`
> As a **user**, I want to see actual load vs forecast on the same chart, so that I can assess grid balance at a glance.

---

**US-015** `[DONE]`
> As a **user**, I want to see a generation mix as a stacked area chart and a donut chart, so that I can understand which energy sources are producing electricity.

---

**US-016** `[DONE]`
> As a **user**, I want to see renewables forecast vs actual, so that I can evaluate forecast accuracy for variable sources.

---

**US-017** `[DONE]`
> As a **user**, I want to see installed capacity as a bar chart, so that I can understand the maximum potential of each technology.

---

**US-018** `[DONE]`
> As a **user**, I want to see a summary of cross-border net flows, so that I can understand France's import/export balance at a glance.

---

## Epic 5 — Dashboard — Load Details Tab

**Goal:** Deep analysis of actual and forecast electricity load.

---

**US-019** `[DONE]`
> As a **user**, I want a detailed actual vs forecast load chart, so that I can examine load patterns closely.

---

**US-020** `[DONE]`
> As a **user**, I want to see forecast error over time (filled to zero), so that I can identify when forecasts were systematically wrong.

---

**US-021** `[DONE]`
> As a **user**, I want to see the average daily load profile by hour, so that I can understand typical consumption patterns throughout the day.

---

**US-022** `[DONE]`
> As a **user**, I want to see load statistics (min, max, mean, std) and a histogram, so that I can understand the distribution of load values.

---

**US-023** `[DONE]`
> As a **user**, I want a daily summary table showing actual GWh, forecast GWh, and error per day, so that I can review load data in tabular form.

---

## Epic 6 — Dashboard — Generation Details Tab

**Goal:** Deep analysis of electricity generation by technology.

---

**US-024** `[DONE]`
> As a **user**, I want a stacked area chart of generation by technology, so that I can see how the energy mix evolves over time.

---

**US-025** `[DONE]`
> As a **user**, I want a donut chart and a horizontal bar chart showing average MW per technology, so that I can compare the relative contribution of each source.

---

**US-026** `[DONE]`
> As a **user**, I want KPIs for total GWh, nuclear share, and renewable share, so that I can quickly assess the low-carbon profile of generation.

---

**US-027** `[DONE]`
> As a **user**, I want a daily generation summary table (date × technology), so that I can review generation data in tabular form.

---

## Epic 7 — Dashboard — Installed Capacity Tab

**Goal:** Analysis of generation infrastructure capacity.

---

**US-028** `[DONE]`
> As a **user**, I want to see installed capacity per technology as a horizontal bar and donut chart, so that I can understand the infrastructure mix.

---

**US-029** `[DONE]`
> As a **user**, I want to see capacity vs average generation side by side, so that I can visually assess how well each technology is being utilised.

---

**US-030** `[DONE]`
> As a **user**, I want a capacity factor table per technology, so that I can understand utilisation rates numerically.

---

**US-031** `[DONE]`
> As a **user**, I want KPIs for total installed GW and top 3 technologies, so that I can identify the dominant infrastructure at a glance.

---

## Epic 8 — Dashboard — Wind & Solar Details Tab

**Goal:** Deep analysis of renewable energy forecast vs actual.

---

**US-032** `[DONE]`
> As a **user**, I want separate forecast vs actual charts for Solar, Wind Onshore, and Wind Offshore, so that I can analyse each renewable source independently.

---

**US-033** `[DONE]`
> As a **user**, I want to see forecast error with a zero reference line, so that I can identify over- and under-forecasting per source.

---

**US-034** `[DONE]`
> As a **user**, I want to see the average hourly daily profile for renewables, so that I can understand their generation patterns throughout the day.

---

**US-035** `[DONE]`
> As a **user**, I want KPIs with capacity factors per renewable source, so that I can compare performance against installed capacity.

---

**US-036** `[DONE]`
> As a **user**, I want a daily GWh pivot table per renewable source, so that I can review renewable data in tabular form.

---

## Epic 9 — Dashboard — Cross-Border Details Tab

**Goal:** Deep analysis of electricity flows between France and neighbouring countries.

---

**US-037** `[DONE]`
> As a **user**, I want to see a net imports line chart for all neighbours combined, so that I can track France's overall import/export balance.

---

**US-038** `[DONE]`
> As a **user**, I want per-neighbour charts (import / export / net) in a 3×2 grid, so that I can compare flows with each country individually.

---

**US-039** `[DONE]`
> As a **user**, I want a daily net import stacked bar chart, so that I can see how each neighbour contributes to the daily balance.

---

**US-040** `[DONE]`
> As a **user**, I want a total energy exchanged grouped bar chart, so that I can compare gross import and export volumes per neighbour.

---

**US-041** `[DONE]`
> As a **user**, I want KPIs showing total net GWh, largest importer, and largest exporter, so that I can identify the most significant trade relationships.

---

**US-042** `[DONE]`
> As a **user**, I want a daily net import summary table, so that I can review cross-border data in tabular form.

---

## Epic 10 — Configuration & UX Improvements

---

**US-047** `[DONE]`
> As a **user**, I want the sidebar to always show the date and time of the last data download, so that I know how fresh the data is even before any in-session refresh has occurred.

**Acceptance criteria:**
- The sidebar always shows a "Last download" timestamp, even on first load when no in-session refresh has happened yet
- When no in-session refresh has occurred, the timestamp is derived from the file modification time of `data/processed/prices.csv`
- When an in-session refresh has occurred (background or manual), the in-memory `_last_data_update` timestamp takes precedence over the file mtime
- If neither source is available (no processed data file exists), the sidebar shows "No data yet"
- The timestamp format is consistent: `YYYY-MM-DD HH:MM:SS`

---

**US-046** `[DONE]`
> As a **user**, I want a "Refresh now" button in the sidebar, so that I can trigger a full data refresh (download + process + chart reload) on demand without waiting for the automatic 15-minute cycle.

**Acceptance criteria:**
- A "Refresh now" button is visible in the sidebar
- Clicking the button triggers `collect_france.main()` followed by `process_france.main()`, exactly as the background refresh does
- While a refresh is in progress (whether triggered manually or by the background thread), the button is disabled and a spinner or in-progress label is shown
- On success, the sidebar last-update timestamp updates and all charts reload with fresh data (via `st.cache_data.clear()`)
- On failure, the sidebar error warning banner displays the error message, consistent with the existing background-refresh error behaviour
- The button reuses the existing shared-state variables (`_refresh_lock`, `_refresh_in_progress`, `_last_data_update`, `_refresh_last_error`) — no new global state introduced

**Defect (QA):** Criterion — "all charts reload with fresh data after cache clear"
**Observed:** After `st.cache_data.clear()` (triggered by the manual refresh), all data loaders raise `AttributeError: 'Index' object has no attribute 'tz'`, crashing every chart.
**Expected:** Loaders return a valid `DatetimeIndex`-indexed DataFrame; `filter_by_date` succeeds.
**Root cause:** pandas 2.x `read_csv(parse_dates=True)` produces a plain `object` `Index` (not a `DatetimeIndex`) when the CSV contains **mixed UTC offsets** (e.g. `+0100` and `+0200`). This occurs because the 30-day collection window (US-045) now crosses the France DST boundary (UTC+1 → UTC+2, last Sunday of March). The bug was latent before US-046 — the `@st.cache_data` decorators masked it by never re-reading the CSVs.
**Fix required:** In each data loader in `dashboard.py`, add `df.index = pd.to_datetime(df.index, utc=True)` after `pd.read_csv(...)` to normalise mixed-offset timestamps into a proper UTC `DatetimeIndex`.
**Regression tests:** `tests/test_dashboard_loaders.py` — 2 tests currently failing, will pass after the fix.

---

**US-045** `[DONE]`
> As a **user**, I want the dashboard to default to showing the last 30 days of data, so that I can see trends and patterns over a meaningful time horizon without adjusting the date range manually.

**Acceptance criteria:**
- The default start date in the sidebar date range selector is set to 30 days before today (instead of 7 days)
- The data collection window in `collect_france.py` is extended to fetch at least 30 days of historical data for all datasets (prices, load, generation, wind/solar forecast, installed capacity, cross-border flows)
- All charts and tables render correctly across the full 30-day window
- The user can still manually adjust the date range to any period within the available data
