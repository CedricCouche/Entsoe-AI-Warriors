"""Collect energy data from ENTSO-E API for France."""

import os
from datetime import UTC, datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

COUNTRY_CODE = "FR"

# Output directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def get_client() -> EntsoePandasClient:
    load_dotenv()
    api_key = os.environ["ENTSOE_API_KEY"]
    return EntsoePandasClient(api_key=api_key)


def default_period() -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return a default period: last 7 days."""
    end = pd.Timestamp(datetime.now(UTC), tz="Europe/Paris")
    start = end - timedelta(days=7)
    return start, end


def collect_day_ahead_prices(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Series:
    print(f"Fetching day-ahead prices for {COUNTRY_CODE}...")
    return client.query_day_ahead_prices(COUNTRY_CODE, start=start, end=end)


def collect_load(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    print(f"Fetching load (actual + forecast) for {COUNTRY_CODE}...")
    return client.query_load_and_forecast(COUNTRY_CODE, start=start, end=end)


def collect_generation_by_type(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    print(f"Fetching actual generation per type for {COUNTRY_CODE}...")
    return client.query_generation(COUNTRY_CODE, start=start, end=end, psr_type=None)


def collect_wind_solar_forecast(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    print(f"Fetching wind & solar forecast for {COUNTRY_CODE}...")
    return client.query_wind_and_solar_forecast(COUNTRY_CODE, start=start, end=end)


def collect_installed_capacity(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    print(f"Fetching installed generation capacity for {COUNTRY_CODE}...")
    return client.query_installed_generation_capacity(
        COUNTRY_CODE, start=start, end=end
    )


def collect_crossborder_flows(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, pd.Series]:
    """Collect cross-border physical flows between France and neighbours."""
    neighbours = {
        "BE": "10YBE----------2",
        "DE_LU": "10Y1001A1001A82H",
        "ES": "10YES-REE------0",
        "GB": "10YGB----------A",
        "IT_NORD": "10Y1001A1001A73I",
        "CH": "10YCH-SWISSGRIDZ",
    }
    fr_code = "10YFR-RTE------C"
    flows = {}
    for name, code in neighbours.items():
        print(f"  Fetching flows FR -> {name}...")
        try:
            flows[f"FR_to_{name}"] = client.query_crossborder_flows(
                fr_code, code, start=start, end=end
            )
        except Exception as e:
            print(f"    Skipped FR -> {name}: {e}")
        print(f"  Fetching flows {name} -> FR...")
        try:
            flows[f"{name}_to_FR"] = client.query_crossborder_flows(
                code, fr_code, start=start, end=end
            )
        except Exception as e:
            print(f"    Skipped {name} -> FR: {e}")
    return flows


def save(data: pd.DataFrame | pd.Series, name: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{name}.csv")
    data.to_csv(path)
    print(f"  Saved {path}")


def main() -> None:
    client = get_client()
    start, end = default_period()
    print(f"Period: {start} -> {end}\n")

    # Day-ahead prices
    prices = collect_day_ahead_prices(client, start, end)
    save(prices, "france_day_ahead_prices")

    # Load (actual + forecast)
    load = collect_load(client, start, end)
    save(load, "france_load")

    # Generation by type
    generation = collect_generation_by_type(client, start, end)
    save(generation, "france_generation_by_type")

    # Wind & solar forecast
    ws_forecast = collect_wind_solar_forecast(client, start, end)
    save(ws_forecast, "france_wind_solar_forecast")

    # Installed capacity
    capacity = collect_installed_capacity(client, start, end)
    save(capacity, "france_installed_capacity")

    # Cross-border flows
    flows = collect_crossborder_flows(client, start, end)
    for name, series in flows.items():
        save(series, f"france_crossborder_{name}")

    print("\nDone! All data saved to data/")


if __name__ == "__main__":
    main()
