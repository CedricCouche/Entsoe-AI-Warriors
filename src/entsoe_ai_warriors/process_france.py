"""Process raw ENTSO-E CSV data into clean, analysis-ready CSVs."""

import logging
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PROCESSED_DIR = DATA_DIR / "processed"

NEIGHBOURS = ["BE", "CH", "DE_LU", "ES", "GB", "IT_NORD"]

COL_PRICE = "Price"
COL_ACTUAL_LOAD = "Actual Load"
COL_FORECAST_LOAD = "Forecasted Load"
COL_IMPORT = "Import"
COL_EXPORT = "Export"
COL_NET_IMPORT = "Net Import"

logger = logging.getLogger(__name__)


def process_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_day_ahead_prices.csv", index_col=0, parse_dates=True)
    df.columns = [COL_PRICE]
    df.index.name = "timestamp"
    if df.empty:
        raise ValueError("Price data is empty")
    return df


def process_load() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_load.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    for col in (COL_ACTUAL_LOAD, COL_FORECAST_LOAD):
        if col not in df.columns:
            raise ValueError(f"Load data missing expected column: {col}")
    if df.empty:
        raise ValueError("Load data is empty")
    return df


def process_generation() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_DIR / "france_generation_by_type.csv",
        header=[0, 1], index_col=0, parse_dates=True,
    )
    df.index.name = "timestamp"
    agg_cols = [(t, sub) for t, sub in df.columns if sub == "Actual Aggregated"]
    if not agg_cols:
        raise ValueError("Generation data has no 'Actual Aggregated' columns — CSV format may have changed")
    df_agg = df[agg_cols].copy()
    df_agg.columns = [t for t, _ in df_agg.columns]
    if df_agg.empty:
        raise ValueError("Generation data is empty after filtering")
    return df_agg


def process_wind_solar_forecast() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_wind_solar_forecast.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    return df


def process_installed_capacity() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "france_installed_capacity.csv", index_col=0, parse_dates=True)
    df.index.name = "timestamp"
    return df


def process_crossborder() -> dict[str, pd.DataFrame]:
    flows: dict[str, pd.DataFrame] = {}
    for nb in NEIGHBOURS:
        export_path = DATA_DIR / f"france_crossborder_FR_to_{nb}.csv"
        import_path = DATA_DIR / f"france_crossborder_{nb}_to_FR.csv"
        exp = pd.read_csv(export_path, index_col=0, parse_dates=True)
        imp = pd.read_csv(import_path, index_col=0, parse_dates=True)
        exp.columns = [COL_EXPORT]
        imp.columns = [COL_IMPORT]
        combined = imp.join(exp, how="outer")
        combined[COL_NET_IMPORT] = combined[COL_IMPORT] - combined[COL_EXPORT]
        combined.index.name = "timestamp"
        flows[nb] = combined
    return flows


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    steps = [
        ("prices", process_prices, "prices.csv"),
        ("load", process_load, "load.csv"),
        ("generation", process_generation, "generation.csv"),
        ("wind_solar_forecast", process_wind_solar_forecast, "wind_solar_forecast.csv"),
        ("installed_capacity", process_installed_capacity, "installed_capacity.csv"),
    ]

    succeeded = 0
    failed = 0
    for name, fn, filename in steps:
        try:
            df = fn()
            df.to_csv(PROCESSED_DIR / filename)
            logger.info("Processed %s -> %s", name, filename)
            succeeded += 1
        except Exception:
            failed += 1
            logger.exception("Failed to process %s", name)

    try:
        flows = process_crossborder()
        for nb, df in flows.items():
            df.to_csv(PROCESSED_DIR / f"crossborder_{nb}.csv")
            logger.info("Processed crossborder %s", nb)
        succeeded += 1
    except Exception:
        failed += 1
        logger.exception("Failed to process cross-border flows")

    logger.info("Processing done: %d succeeded, %d failed.", succeeded, failed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
