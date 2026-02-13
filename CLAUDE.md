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
| `src/entsoe_ai_warriors/dashboard.py` | Streamlit + Plotly interactive dashboard |

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
