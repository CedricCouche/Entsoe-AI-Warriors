import logging
from pathlib import Path

import pandas as pd

from entsoe_ai_warriors.client import get_client

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

COUNTRY_CODE = "FR"
FRANCE_EIC = "10YFR-RTE------C"

NEIGHBOURS = {
    "BE": "10YBE----------2",
    "DE_LU": "10Y1001A1001A82H",
    "ES": "10YES-REE------0",
    "GB": "10YGB----------A",
    "IT_NORD": "10Y1001A1001A73I",
    "CH": "10YCH-SWISSGRIDZ",
}


def _get_period() -> tuple[pd.Timestamp, pd.Timestamp]:
    now = pd.Timestamp.now(tz="Europe/Paris")
    start = (now - pd.Timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    client = get_client()
    start, end = _get_period()

    try:
        df = client.query_day_ahead_prices(COUNTRY_CODE, start=start, end=end)
        df.to_csv(DATA_DIR / "france_day_ahead_prices.csv")
        logger.info("Collected day-ahead prices")
    except Exception:
        logger.exception("Failed to collect day-ahead prices")

    try:
        df = client.query_load_and_forecast(COUNTRY_CODE, start=start, end=end)
        df.to_csv(DATA_DIR / "france_load.csv")
        logger.info("Collected load")
    except Exception:
        logger.exception("Failed to collect load")

    try:
        df = client.query_generation(COUNTRY_CODE, start=start, end=end, psr_type=None)
        df.to_csv(DATA_DIR / "france_generation_by_type.csv")
        logger.info("Collected generation by type")
    except Exception:
        logger.exception("Failed to collect generation by type")

    try:
        df = client.query_wind_and_solar_forecast(COUNTRY_CODE, start=start, end=end, psr_type=None)
        df.to_csv(DATA_DIR / "france_wind_solar_forecast.csv")
        logger.info("Collected wind/solar forecast")
    except Exception:
        logger.exception("Failed to collect wind/solar forecast")

    try:
        df = client.query_installed_generation_capacity(COUNTRY_CODE, start=start, end=end, psr_type=None)
        df.to_csv(DATA_DIR / "france_installed_capacity.csv")
        logger.info("Collected installed capacity")
    except Exception:
        logger.exception("Failed to collect installed capacity")

    for nb, nb_eic in NEIGHBOURS.items():
        try:
            df = client.query_crossborder_flows(FRANCE_EIC, nb_eic, start=start, end=end)
            df.to_csv(DATA_DIR / f"france_crossborder_FR_to_{nb}.csv")
            logger.info("Collected FR -> %s flows", nb)
        except Exception:
            logger.exception("Failed to collect FR -> %s flows", nb)

        try:
            df = client.query_crossborder_flows(nb_eic, FRANCE_EIC, start=start, end=end)
            df.to_csv(DATA_DIR / f"france_crossborder_{nb}_to_FR.csv")
            logger.info("Collected %s -> FR flows", nb)
        except Exception:
            logger.exception("Failed to collect %s -> FR flows", nb)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
