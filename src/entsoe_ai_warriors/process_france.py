import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PROCESSED_DIR = DATA_DIR / "processed"

NEIGHBOURS = ["BE", "CH", "DE_LU", "ES", "GB", "IT_NORD"]

COL_PRICE = "Price"
COL_ACTUAL_LOAD = "Actual Load"
COL_FORECAST_LOAD = "Forecasted Load"
COL_IMPORT = "Import"
COL_EXPORT = "Export"
COL_NET_IMPORT = "Net Import"


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Prices
    try:
        df = pd.read_csv(DATA_DIR / "france_day_ahead_prices.csv", index_col=0, parse_dates=True)
        if df.empty:
            raise ValueError("Prices data is empty")
        df.columns = [COL_PRICE]
        df.index.name = "timestamp"
        df.to_csv(PROCESSED_DIR / "prices.csv")
        logger.info("Processed prices")
    except Exception:
        logger.exception("Failed to process prices")

    # Load
    try:
        df = pd.read_csv(DATA_DIR / "france_load.csv", index_col=0, parse_dates=True)
        if df.empty:
            raise ValueError("Load data is empty")
        if COL_ACTUAL_LOAD not in df.columns or COL_FORECAST_LOAD not in df.columns:
            raise ValueError(f"Missing expected load columns. Found: {df.columns.tolist()}")
        df.index.name = "timestamp"
        df.to_csv(PROCESSED_DIR / "load.csv")
        logger.info("Processed load")
    except Exception:
        logger.exception("Failed to process load")

    # Generation
    try:
        df = pd.read_csv(
            DATA_DIR / "france_generation_by_type.csv",
            header=[0, 1], index_col=0, parse_dates=True,
        )
        actual_cols = [col for col in df.columns if col[1] == "Actual Aggregated"]
        if not actual_cols:
            raise ValueError("No 'Actual Aggregated' columns found in generation data")
        df = df[actual_cols].copy()
        df.columns = [col[0] for col in df.columns]
        if df.empty:
            raise ValueError("Generation data is empty after filtering")
        df.index.name = "timestamp"
        df.to_csv(PROCESSED_DIR / "generation.csv")
        logger.info("Processed generation")
    except Exception:
        logger.exception("Failed to process generation")

    # Wind & solar forecast
    try:
        df = pd.read_csv(DATA_DIR / "france_wind_solar_forecast.csv", index_col=0, parse_dates=True)
        df.index.name = "timestamp"
        df.to_csv(PROCESSED_DIR / "wind_solar_forecast.csv")
        logger.info("Processed wind/solar forecast")
    except Exception:
        logger.exception("Failed to process wind/solar forecast")

    # Installed capacity
    try:
        df = pd.read_csv(DATA_DIR / "france_installed_capacity.csv", index_col=0, parse_dates=True)
        df.index.name = "timestamp"
        df.to_csv(PROCESSED_DIR / "installed_capacity.csv")
        logger.info("Processed installed capacity")
    except Exception:
        logger.exception("Failed to process installed capacity")

    # Cross-border flows (per-neighbour failures handled individually)
    for nb in NEIGHBOURS:
        try:
            export_df = pd.read_csv(
                DATA_DIR / f"france_crossborder_FR_to_{nb}.csv", index_col=0, parse_dates=True
            )
            import_df = pd.read_csv(
                DATA_DIR / f"france_crossborder_{nb}_to_FR.csv", index_col=0, parse_dates=True
            )
            export_df.columns = [COL_EXPORT]
            import_df.columns = [COL_IMPORT]
            df = import_df.join(export_df, how="outer")
            df[COL_NET_IMPORT] = df[COL_IMPORT] - df[COL_EXPORT]
            df.index.name = "timestamp"
            df.to_csv(PROCESSED_DIR / f"crossborder_{nb}.csv")
            logger.info("Processed crossborder %s", nb)
        except Exception:
            logger.exception("Failed to process crossborder %s", nb)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
