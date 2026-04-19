"""
Regression tests for the CSV loader pattern used in dashboard.py.

Root cause (filed against US-046): when the 30-day collection window (introduced by
US-045) crosses a DST boundary, the processed CSVs contain timestamps with mixed UTC
offsets (e.g. +0100 before the transition and +0200 after). pandas 2.x read_csv with
parse_dates=True falls back to a plain object Index instead of a DatetimeIndex,
causing filter_by_date to raise AttributeError: 'Index' object has no attribute 'tz'.
"""

import io

import pandas as pd
import pytest


# --- helpers ------------------------------------------------------------------

def _read_csv_as_loaders_do(csv_text: str) -> pd.DataFrame:
    """Reproduces exactly what load_prices / load_load / etc. do in dashboard.py."""
    df = pd.read_csv(io.StringIO(csv_text), index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


# --- regression tests ---------------------------------------------------------

class TestLoaderIndexType:
    """The index returned by the loader pattern must be a DatetimeIndex."""

    def test_single_offset_produces_datetimeindex(self):
        csv = "timestamp,Price\n2026-04-01 00:00:00+0200,85.3\n2026-04-01 00:15:00+0200,86.1\n"
        df = _read_csv_as_loaders_do(csv)
        assert isinstance(df.index, pd.DatetimeIndex), (
            f"Expected DatetimeIndex, got {type(df.index).__name__} (dtype={df.index.dtype})"
        )

    def test_mixed_offsets_across_dst_boundary_produces_datetimeindex(self):
        # France transitions from UTC+1 to UTC+2 on the last Sunday of March.
        # A 30-day window starting in mid-March spans this boundary.
        csv = (
            "timestamp,Price\n"
            "2026-03-28 23:45:00+0100,85.3\n"   # before DST
            "2026-03-29 03:00:00+0200,88.1\n"   # after DST
            "2026-04-01 12:00:00+0200,90.0\n"
        )
        df = _read_csv_as_loaders_do(csv)
        assert isinstance(df.index, pd.DatetimeIndex), (
            "Mixed UTC offsets (DST boundary) caused read_csv to return a plain object "
            f"Index instead of DatetimeIndex. dtype={df.index.dtype}. "
            "Fix: add pd.to_datetime(df.index, utc=True) in each loader."
        )

    def test_datetimeindex_has_tz_attribute(self):
        """filter_by_date accesses df.index.tz — must not raise AttributeError."""
        csv = (
            "timestamp,Price\n"
            "2026-03-28 23:45:00+0100,85.3\n"
            "2026-03-29 03:00:00+0200,88.1\n"
        )
        df = _read_csv_as_loaders_do(csv)
        # This is the exact line that raises in filter_by_date
        try:
            _ = df.index.tz
        except AttributeError:
            pytest.fail(
                "df.index.tz raised AttributeError — index is not a DatetimeIndex. "
                "This causes all dashboard charts to fail after a cache clear."
            )
