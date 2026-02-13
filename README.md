# Entsoe-AI-Warriors

Interactive dashboard and data pipeline for French electricity data from the [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/).

## Features

- **Day-ahead prices** — hourly electricity spot prices for France
- **Load monitoring** — actual vs forecasted electrical load
- **Generation mix** — stacked area chart and donut breakdown by source (nuclear, wind, solar, hydro, gas, etc.)
- **Renewables** — wind & solar forecast vs actual generation, plus installed capacity by technology
- **Cross-border flows** — net imports/exports with 6 neighbours (Belgium, Switzerland, Germany/Luxembourg, Spain, Great Britain, Italy North)
- **Auto-refresh** — background thread re-fetches data from the ENTSO-E API every 15 minutes; the sidebar shows the last download timestamp

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- An ENTSO-E API key (free — [register here](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html))

## Setup

```bash
# Clone the repository
git clone git@github.com:CedricCouche/Entsoe-AI-Warriors.git
cd Entsoe-AI-Warriors

# Install dependencies
uv sync

# Create a .env file with your API key
echo "ENTSOE_API_KEY=your-key-here" > .env
```

## Usage

### Launch the dashboard

```bash
uv run streamlit run src/entsoe_ai_warriors/dashboard.py
```

The dashboard opens in your browser and automatically refreshes data every 15 minutes.

### Collect data manually

```bash
uv run python -m entsoe_ai_warriors.collect_france
```

This fetches the last 7 days of French energy data and saves 17 CSV files to the `data/` directory.

## Project structure

```
src/entsoe_ai_warriors/
    client.py              # ENTSO-E API client wrapper
    collect_france.py      # Data collection script
    dashboard.py           # Streamlit + Plotly dashboard (with background auto-refresh)
data/                      # CSV files (prices, load, generation, forecasts, cross-border flows)
```

## Tech stack

- [entsoe-py](https://github.com/EnergieID/entsoe-py) — ENTSO-E API client
- [Streamlit](https://streamlit.io/) — web dashboard framework
- [Plotly](https://plotly.com/python/) — interactive charts
- [python-dotenv](https://github.com/theskumar/python-dotenv) — environment variable management

## License

This project is for educational and research purposes.
