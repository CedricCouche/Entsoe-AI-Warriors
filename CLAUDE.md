# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Entsoe-AI-Warriors — ENTSO-E (European Network of Transmission System Operators for Electricity) energy data collection and interactive dashboard for France.

## Repository

- Remote: `git@github.com:CedricCouche/Entsoe-AI-Warriors.git`
- Branch: `main` — stable, production-ready
- Branch: `dev-claude` — dedicated to all work done with Claude Code (merge into `main` when ready)

## Architecture

- **Runtime:** Python 3.12+, managed with `uv`
- **Package:** `src/entsoe_ai_warriors/` (Hatch build system)
- **Data:** `data/` — raw CSV files from ENTSO-E API; `data/processed/` — cleaned, analysis-ready CSVs produced by `process_france.py`

### Skills / Reference docs

Reference `SKILL.md` files are stored under `.claude/` at the project root:

| Folder | Topic |
|--------|-------|
| `.claude/PYTHON/` | Python language reference |
| `.claude/UV/` | `uv` package manager |
| `.claude/Streamlit/` | Streamlit framework |
| `.claude/Plotly/` | Plotly charting library |
| `.claude/GraphicChart/` | Graphic chart design patterns |
| `.claude/ENSTOE-API/` | ENTSO-E API usage |

### Key files

| File | Purpose |
|------|---------|
| `src/entsoe_ai_warriors/client.py` | ENTSO-E API client wrapper (single source of truth for `get_client()`) |
| `src/entsoe_ai_warriors/collect_france.py` | **Download** — fetches raw data from ENTSO-E API, saves to `data/` |
| `src/entsoe_ai_warriors/process_france.py` | **Process** — reads raw CSVs, transforms (flatten multi-headers, compute net imports, rename columns), saves to `data/processed/`; also exports `COL_*` constants and `PROCESSED_DIR` |
| `src/entsoe_ai_warriors/dashboard.py` | **Render** — reads from `data/processed/`, filters by date, renders all charts; no data transformation |

### Dashboard tabs

The dashboard has 6 tabs, all using the Adalan corporate theme (Plotly template `adalan`) and `SOURCE_COLORS` for per-source colouring:

1. **⚡ Overview** — KPIs, day-ahead prices, load actual vs forecast, generation mix (stacked area + donut), renewables forecast vs actual, installed capacity bar, cross-border flows
2. **🔌 Load Details** — larger actual vs forecast chart, forecast error (fill-to-zero), average daily profile by hour, statistics (min/max/mean/std, histogram, daily summary table)
3. **🏭 Generation Details** — stacked area chart, donut + horizontal bar of average MW per source, KPIs (total GWh, nuclear %, renewable %), daily generation summary table
4. **🔋 Installed Capacity** — horizontal bar + donut, capacity vs average generation side-by-side bar, KPIs (total GW, top 3 technologies), capacity factor table per technology
5. **🌿 Wind & Solar Details** — per-source forecast vs actual (Solar, Wind Onshore, Wind Offshore), forecast error with zero line, hourly daily profile, KPIs with capacity factors, daily GWh pivot table
6. **🔀 Cross-Border Details** — net imports line chart, per-neighbour import/export/net charts (3x2 grid), daily net import stacked bar, total energy exchanged grouped bar, KPIs (total net GWh, largest importer/exporter), daily net import summary table

### Key constants and helpers

- `MW_TO_GWH` / `_to_gwh()` — converts sum of 15-min MW readings to GWh; `INTERVAL_HOURS = 0.25` (15 min), `MW_TO_GWH = INTERVAL_HOURS / 1000` (dashboard.py)
- `_safe_pct()` — division-safe percentage computation (dashboard.py)
- `COL_*` constants — single source of truth for CSV column names, defined in `process_france.py` and imported by `dashboard.py`
- `PROCESSED_DIR` — path to `data/processed/`, defined in `process_france.py` and imported by `dashboard.py`
- `NEIGHBOURS` — list of 6 neighbour codes `["BE", "CH", "DE_LU", "ES", "GB", "IT_NORD"]`, defined in both `process_france.py` and `dashboard.py`
- `SOURCE_COLORS` — per-source colour overrides for Solar and Hydro variants; other technologies fall back to `ADALAN_COLORS` palette (dashboard.py)

### Background data refresh

The dashboard spawns a daemon thread that calls `collect_france.main()` then `process_france.main()` every 15 minutes (`REFRESH_INTERVAL_SECONDS = 900`). A second constant `POLL_INTERVAL_SECONDS = 30` controls how often each Streamlit session checks for new data. The sidebar displays the last download timestamp and shows a warning if the last refresh failed. Requires `ENTSOE_API_KEY` in `.env`.

### Error handling

- `collect_france.main()` wraps each collection step independently — partial failures don't prevent other data from being saved
- Cross-border flow collection handles per-neighbour failures gracefully
- Dashboard data loaders validate CSV structure on load and show clear error messages
- Background refresh failures are surfaced in the sidebar

### Dependencies

- `entsoe-py>=0.7` — ENTSO-E Transparency Platform API client
- `streamlit>=1.30` — web dashboard framework
- `plotly>=6.0` — interactive charts
- `python-dotenv>=1.0` — environment variable management
- **Dev:** `pytest`, `ruff`, `mypy` (via `uv sync --extra dev`)

## Common commands

```bash
# Install dependencies
uv sync

# Install with dev tools
uv sync --extra dev

# Launch the dashboard
uv run streamlit run src/entsoe_ai_warriors/dashboard.py

# Collect data from ENTSO-E API (requires ENTSOE_API_KEY in .env)
uv run python -m entsoe_ai_warriors.collect_france

# Process raw CSVs into analysis-ready data
uv run python -m entsoe_ai_warriors.process_france
```
