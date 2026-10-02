# db/models.py
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()


def _utc_now() -> datetime:
    return datetime.now(UTC)


weather_observations = Table(
    "weather_observations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("station", String, nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("temp_c", Float),
    Column("rainfall_mm", Float),
    Column("humidity_pct", Float),
    Column("is_outlier", Boolean, nullable=False, default=False),
    Column(
        "ingested_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    ),
    UniqueConstraint("station", "observed_at", name="uq_weather_station_observed"),
)

nse_prices = Table(
    "nse_prices",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String, nullable=False),
    Column("trading_date", DateTime(timezone=True), nullable=False),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Float),
    Column("daily_change_pct", Float),
    Column(
        "ingested_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    ),
    UniqueConstraint("ticker", "trading_date", name="uq_nse_ticker_date"),
)

cbk_rates = Table(
    "cbk_rates",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("currency", String, nullable=False),
    Column("rate_date", DateTime(timezone=True), nullable=False),
    Column("buying", Float),
    Column("selling", Float),
    Column("mean", Float),
    Column(
        "ingested_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    ),
    UniqueConstraint("currency", "rate_date", name="uq_cbk_currency_date"),
)

pipeline_runs = Table(
    "pipeline_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("pipeline_name", String, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=True),
    Column("status", String, nullable=False),
    Column("rows_loaded", Integer, nullable=False, default=0),
    Column("error", Text, nullable=True),
)

dq_results = Table(
    "dq_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", Integer, nullable=False),
    Column("check_name", String, nullable=False),
    Column("passed", Boolean, nullable=False),
    Column("details", Text, nullable=True),
    Column(
        "run_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    ),
)

