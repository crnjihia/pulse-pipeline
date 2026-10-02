# tests/test_quality.py
from datetime import UTC, datetime, timedelta

from sqlalchemy import Column, Integer, MetaData, String, Table

from db import models
from etl.quality.checks import (
    check_duplicates,
    check_not_null,
    check_row_count,
    run_quality_checks,
)


def _now() -> datetime:
    return datetime.now(UTC)


def test_quality_checks_weather_pass(sqlite_engine):
    recent_ts = _now() - timedelta(minutes=15)
    with sqlite_engine.begin() as conn:
        conn.execute(
            models.weather_observations.insert().values(
                station="NairobiHQ",
                observed_at=recent_ts,
                temp_c=23.0,
                rainfall_mm=0.0,
                humidity_pct=70.0,
                is_outlier=False,
                ingested_at=_now(),
            )
        )

    passed = run_quality_checks("weather", run_id=1, engine=sqlite_engine, max_age_hours=26)
    assert passed is True

    # Verify dq_results was written
    with sqlite_engine.begin() as conn:
        results = conn.execute(models.dq_results.select()).fetchall()
        assert len(results) >= 4
        assert all(r.passed for r in results)


def test_quality_freshness_fail(sqlite_engine):
    stale_ts = _now() - timedelta(hours=30)
    with sqlite_engine.begin() as conn:
        conn.execute(
            models.cbk_rates.insert().values(
                currency="USD",
                rate_date=stale_ts,
                buying=129.0,
                selling=130.0,
                mean=129.5,
                ingested_at=_now(),
            )
        )

    passed = run_quality_checks("cbk", run_id=2, engine=sqlite_engine, max_age_hours=26)
    assert passed is False


def test_quality_not_null_fail(sqlite_engine):
    recent_ts = _now() - timedelta(hours=1)
    with sqlite_engine.begin() as conn:
        conn.execute(
            models.nse_prices.insert().values(
                ticker="TEST",
                trading_date=recent_ts,
                open=10.0,
                close=None,  # Null close should fail check
                volume=100.0,
                daily_change_pct=0.0,
                ingested_at=_now(),
            )
        )

    passed = check_not_null(
        sqlite_engine,
        models.nse_prices,
        ["ticker", "trading_date", "close"],
        run_id=3,
    )
    assert passed is False


def test_quality_row_count_empty(sqlite_engine):
    passed = check_row_count(sqlite_engine, models.weather_observations, run_id=4)
    assert passed is False


def test_quality_check_duplicates(sqlite_engine):
    meta = MetaData()
    test_table = Table(
        "test_dup_check",
        meta,
        Column("id", Integer, primary_key=True),
        Column("station", String),
        Column("observed_at", String),
    )
    meta.create_all(sqlite_engine)

    with sqlite_engine.begin() as conn:
        conn.execute(
            test_table.insert(),
            [
                {"station": "A", "observed_at": "2026-10-01T00:00:00Z"},
                {"station": "A", "observed_at": "2026-10-01T00:00:00Z"},
            ],
        )

    passed = check_duplicates(
        sqlite_engine,
        test_table,
        ["station", "observed_at"],
        run_id=5,
    )
    assert passed is False

