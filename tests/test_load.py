# tests/test_load.py
from datetime import UTC, datetime

import pandas as pd

from db import models
from etl.load.loader import load_cbk, load_nse, load_weather


def test_load_weather_idempotency(sqlite_engine):
    observed_time = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    df1 = pd.DataFrame(
        [
            {
                "station": "NairobiHQ",
                "observed_at": observed_time,
                "temp_c": 24.5,
                "rainfall_mm": 0.0,
                "humidity_pct": 60.0,
                "is_outlier": False,
            }
        ]
    )
    # First load
    rows1 = load_weather(df1, run_id=1, engine=sqlite_engine)
    assert rows1 == 1

    with sqlite_engine.begin() as conn:
        records = conn.execute(models.weather_observations.select()).fetchall()
        assert len(records) == 1
        assert records[0].temp_c == 24.5

    # Second load with same natural key (station, observed_at) but updated temperature
    df2 = pd.DataFrame(
        [
            {
                "station": "NairobiHQ",
                "observed_at": observed_time,
                "temp_c": 25.5,
                "rainfall_mm": 0.5,
                "humidity_pct": 58.0,
                "is_outlier": False,
            }
        ]
    )
    rows2 = load_weather(df2, run_id=2, engine=sqlite_engine)
    assert rows2 == 1

    # Idempotent: row count remains 1, value updated
    with sqlite_engine.begin() as conn:
        records = conn.execute(models.weather_observations.select()).fetchall()
        assert len(records) == 1
        assert records[0].temp_c == 25.5
        assert records[0].rainfall_mm == 0.5


def test_load_nse_idempotency(sqlite_engine):
    trading_date = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    df1 = pd.DataFrame(
        [
            {
                "ticker": "SCOM",
                "trading_date": trading_date,
                "open": 15.0,
                "high": 16.0,
                "low": 14.8,
                "close": 15.5,
                "volume": 100000.0,
                "daily_change_pct": 3.33,
            }
        ]
    )
    rows1 = load_nse(df1, run_id=1, engine=sqlite_engine)
    assert rows1 == 1

    # Rerun with revised closing price and volume
    df2 = pd.DataFrame(
        [
            {
                "ticker": "SCOM",
                "trading_date": trading_date,
                "open": 15.0,
                "high": 16.2,
                "low": 14.8,
                "close": 15.8,
                "volume": 120000.0,
                "daily_change_pct": 5.33,
            }
        ]
    )
    rows2 = load_nse(df2, run_id=2, engine=sqlite_engine)
    assert rows2 == 1

    with sqlite_engine.begin() as conn:
        records = conn.execute(models.nse_prices.select()).fetchall()
        assert len(records) == 1
        assert records[0].close == 15.8
        assert records[0].volume == 120000.0


def test_load_cbk_idempotency(sqlite_engine):
    rate_date = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    df1 = pd.DataFrame(
        [
            {
                "currency": "USD",
                "rate_date": rate_date,
                "buying": 128.5,
                "selling": 129.5,
                "mean": 129.0,
            }
        ]
    )
    rows1 = load_cbk(df1, run_id=1, engine=sqlite_engine)
    assert rows1 == 1

    df2 = pd.DataFrame(
        [
            {
                "currency": "USD",
                "rate_date": rate_date,
                "buying": 128.6,
                "selling": 129.6,
                "mean": 129.1,
            }
        ]
    )
    rows2 = load_cbk(df2, run_id=2, engine=sqlite_engine)
    assert rows2 == 1

    with sqlite_engine.begin() as conn:
        records = conn.execute(models.cbk_rates.select()).fetchall()
        assert len(records) == 1
        assert records[0].mean == 129.1


def test_load_empty_dataframes(sqlite_engine):
    assert load_weather(pd.DataFrame(), run_id=1, engine=sqlite_engine) == 0
    assert load_nse(pd.DataFrame(), run_id=1, engine=sqlite_engine) == 0
    assert load_cbk(pd.DataFrame(), run_id=1, engine=sqlite_engine) == 0

