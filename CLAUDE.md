# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Entsoe-AI-Warriors — ENTSO-E (European Network of Transmission System Operators for Electricity) energy data collection and interactive dashboard for France.

## Repository

- Remote: `git@github.com:CedricCouche/Entsoe-AI-Warriors.git`
- Branch: `main`

## Architecture

- **Runtime:** Python 3.12+, managed with `uv`
- **Package:** `src/entsoe_ai_warriors/` (Hatch build system)
- **Data:** `data/` — 17 CSV files with 7 days of French energy data (prices, load, generation, wind/solar forecast, installed capacity, cross-border flows with BE/CH/DE_LU/ES/GB/IT_NORD)

### Key files

| File | Purpose |
|------|---------|
| `src/entsoe_ai_warriors/client.py` | ENTSO-E API client wrapper |
| `src/entsoe_ai_warriors/collect_france.py` | Data collection script for France |
| `src/entsoe_ai_warriors/dashboard.py` | Streamlit + Plotly interactive dashboard (with background auto-refresh) |

### Dashboard tabs

The dashboard has 6 tabs, all using the 1970s retro theme (Plotly template `retro_70s`) and `SOURCE_COLORS` for per-source colouring:

1. **⚡ Overview** — KPIs, day-ahead prices, load actual vs forecast, generation mix (stacked area + donut), renewables forecast vs actual, installed capacity bar, cross-border flows
2. **🔌 Load Details** — larger actual vs forecast chart, forecast error (fill-to-zero), average daily profile by hour, statistics (min/max/mean/std, histogram, daily summary table)
3. **🏭 Generation Details** — stacked area chart, donut + horizontal bar of average MW per source, KPIs (total GWh, nuclear %, renewable %), daily generation summary table
4. **🔋 Installed Capacity** — horizontal bar + donut, capacity vs average generation side-by-side bar, KPIs (total GW, top 3 technologies), capacity factor table per technology
5. **🌿 Wind & Solar Details** — per-source forecast vs actual (Solar, Wind Onshore, Wind Offshore), forecast error with zero line, hourly daily profile, KPIs with capacity factors, daily GWh pivot table
6. **🔀 Cross-Border Details** — net imports line chart, per-neighbour import/export/net charts (3x2 grid), daily net import stacked bar, total energy exchanged grouped bar, KPIs (total net GWh, largest importer/exporter), daily net import summary table

### Background data refresh

The dashboard spawns a daemon thread that calls `collect_france.main()` every hour to keep CSV data fresh. The sidebar displays the last download timestamp (based on CSV file modification time). The refresh interval is controlled by `REFRESH_INTERVAL_SECONDS` in `dashboard.py`. Requires `ENTSOE_API_KEY` in `.env`.

### Dependencies

- `entsoe-py` — ENTSO-E Transparency Platform API client
- `streamlit` — web dashboard framework
- `plotly` — interactive charts
- `python-dotenv` — environment variable management

## Common commands

```bash
# Install dependencies
uv sync

# Launch the dashboard
uv run streamlit run src/entsoe_ai_warriors/dashboard.py

# Collect data from ENTSO-E API (requires ENTSOE_API_KEY in .env)
uv run python -m entsoe_ai_warriors.collect_france
```
