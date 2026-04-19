"""
Tests for the _data_file_mtime fallback used in the sidebar timestamp display (US-047).
We test the logic directly without importing dashboard.py (avoids Streamlit context).
"""

import time
from pathlib import Path

import pandas as pd
import pytest


def _data_file_mtime(processed_dir: Path) -> pd.Timestamp | None:
    """Reproduces the _data_file_mtime helper from dashboard.py."""
    p = processed_dir / "prices.csv"
    if p.exists():
        return pd.Timestamp.fromtimestamp(p.stat().st_mtime)
    return None


class TestDataFileMtime:
    def test_returns_none_when_file_absent(self, tmp_path):
        assert _data_file_mtime(tmp_path) is None

    def test_returns_timestamp_when_file_exists(self, tmp_path):
        (tmp_path / "prices.csv").write_text("timestamp,Price\n")
        result = _data_file_mtime(tmp_path)
        assert isinstance(result, pd.Timestamp)

    def test_timestamp_is_recent(self, tmp_path):
        (tmp_path / "prices.csv").write_text("timestamp,Price\n")
        before = pd.Timestamp.now()
        time.sleep(0.01)
        result = _data_file_mtime(tmp_path)
        assert result is not None
        assert result <= pd.Timestamp.now()
        assert result >= before - pd.Timedelta(seconds=5)

    def test_in_session_ts_takes_precedence(self, tmp_path):
        """Simulate the sidebar logic: _ts wins over file mtime."""
        (tmp_path / "prices.csv").write_text("timestamp,Price\n")
        in_session_ts = pd.Timestamp("2026-04-19 10:00:00")
        display_ts = in_session_ts if in_session_ts is not None else _data_file_mtime(tmp_path)
        assert display_ts == in_session_ts

    def test_fallback_used_when_no_in_session_ts(self, tmp_path):
        """Simulate the sidebar logic: mtime used when _ts is None."""
        (tmp_path / "prices.csv").write_text("timestamp,Price\n")
        in_session_ts = None
        display_ts = in_session_ts if in_session_ts is not None else _data_file_mtime(tmp_path)
        assert isinstance(display_ts, pd.Timestamp)
