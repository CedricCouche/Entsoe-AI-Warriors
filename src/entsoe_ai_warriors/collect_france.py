"""Collect energy data from ENTSO-E API for France."""

import logging
import os
from datetime import UTC, datetime, timedelta

import pandas as pd
from entsoe import EntsoePandasClient

from entsoe_ai_warriors.client import get_client

COUNTRY_CODE = "FR"

# Output directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

logger = logging.getLogger(__name__)


def default_period() -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return a default period: last 7 days."""
    end = pd.Timestamp(datetime.now(UTC)).tz_convert("Europe/Paris")
    start = end - timedelta(days=7)
    return start, end


def collect_day_ahead_prices(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.Series:
    logger.info("Fetching day-ahead prices for %s...", COUNTRY_CODE)
    return client.query_day_ahead_prices(COUNTRY_CODE, start=start, end=end)


def collect_load(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    logger.info("Fetching load (actual + forecast) for %s...", COUNTRY_CODE)
    return client.query_load_and_forecast(COUNTRY_CODE, start=start, end=end)


def collect_generation_by_type(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    logger.info("Fetching actual generation per type for %s...", COUNTRY_CODE)
    return client.query_generation(COUNTRY_CODE, start=start, end=end, psr_type=None)


def collect_wind_solar_forecast(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    logger.info("Fetching wind & solar forecast for %s...", COUNTRY_CODE)
    return client.query_wind_and_solar_forecast(COUNTRY_CODE, start=start, end=end)


def collect_installed_capacity(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    logger.info("Fetching installed generation capacity for %s...", COUNTRY_CODE)
    return client.query_installed_generation_capacity(
        COUNTRY_CODE, start=start, end=end
    )


NEIGHBOUR_CODES = {
    "BE": "10YBE----------2",
    "DE_LU": "10Y1001A1001A82H",
    "ES": "10YES-REE------0",
    "GB": "10YGB----------A",
    "IT_NORD": "10Y1001A1001A73I",
    "CH": "10YCH-SWISSGRIDZ",
}
FR_CODE = "10YFR-RTE------C"


def collect_crossborder_flows(
    client: EntsoePandasClient,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, pd.Series]:
    """Collect cross-border physical flows between France and neighbours."""
    flows = {}
    for name, code in NEIGHBOUR_CODES.items():
        logger.info("  Fetching flows FR -> %s...", name)
        try:
            flows[f"FR_to_{name}"] = client.query_crossborder_flows(
                FR_CODE, code, start=start, end=end
            )
        except (ConnectionError, TimeoutError) as e:
            logger.warning("  Skipped FR -> %s (network): %s", name, e)
        except Exception as e:
            logger.warning("  Skipped FR -> %s: %s", name, e)
        logger.info("  Fetching flows %s -> FR...", name)
        try:
            flows[f"{name}_to_FR"] = client.query_crossborder_flows(
                code, FR_CODE, start=start, end=end
            )
        except (ConnectionError, TimeoutError) as e:
            logger.warning("  Skipped %s -> FR (network): %s", name, e)
        except Exception as e:
            logger.warning("  Skipped %s -> FR: %s", name, e)
    return flows


def save(data: pd.DataFrame | pd.Series, name: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{name}.csv")
    data.to_csv(path)
    logger.info("  Saved %s", path)


def main() -> None:
    client = get_client()
    start, end = default_period()
    logger.info("Period: %s -> %s", start, end)

    # Each step is independent — collect and save what we can
    steps: list[tuple[str, str]] = [
        ("day_ahead_prices", "france_day_ahead_prices"),
        ("load", "france_load"),
        ("generation_by_type", "france_generation_by_type"),
        ("wind_solar_forecast", "france_wind_solar_forecast"),
        ("installed_capacity", "france_installed_capacity"),
    ]

    collectors = {
        "day_ahead_prices": collect_day_ahead_prices,
        "load": collect_load,
        "generation_by_type": collect_generation_by_type,
        "wind_solar_forecast": collect_wind_solar_forecast,
        "installed_capacity": collect_installed_capacity,
    }

    succeeded = 0
    failed = 0
    for step_name, csv_name in steps:
        try:
            data = collectors[step_name](client, start, end)
            save(data, csv_name)
            succeeded += 1
        except Exception:
            failed += 1
            logger.exception("Failed to collect %s", step_name)

    # Cross-border flows (individual failures handled inside)
    try:
        flows = collect_crossborder_flows(client, start, end)
        for name, series in flows.items():
            save(series, f"france_crossborder_{name}")
        succeeded += 1
    except Exception:
        failed += 1
        logger.exception("Failed to collect cross-border flows")

    logger.info("Done! %d succeeded, %d failed.", succeeded, failed)
    if failed:
        logger.warning("%d collection(s) failed — some data may be stale.", failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
