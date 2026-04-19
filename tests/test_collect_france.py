import pandas as pd

from entsoe_ai_warriors.collect_france import _get_period


def test_get_period_window_is_30_days():
    start, end = _get_period()
    delta = end - start
    assert delta.days >= 29, f"Expected at least 29 days window, got {delta.days}"
    assert delta.days <= 31, f"Expected at most 31 days window, got {delta.days}"


def test_get_period_start_is_midnight():
    start, _ = _get_period()
    assert start.hour == 0
    assert start.minute == 0
    assert start.second == 0
    assert start.microsecond == 0


def test_get_period_end_is_after_start():
    start, end = _get_period()
    assert end > start


def test_get_period_timezone_is_paris():
    start, end = _get_period()
    assert str(start.tzinfo) == "Europe/Paris"
    assert str(end.tzinfo) == "Europe/Paris"
