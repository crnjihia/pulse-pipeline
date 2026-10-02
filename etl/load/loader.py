# etl/load/loader.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
from sqlalchemy import Table
from sqlalchemy.engine import Engine
from structlog import get_logger

from db import models
from db.session import get_engine

logger = get_logger(__name__)


def _upsert_dataframe(
    df: pd.DataFrame,
    table: Table,
    engine: Engine,
    conflict_cols: list[str],
) -> int:
    """
    Insert or update rows from *df* into *table* using ON CONFLICT DO UPDATE.
    Supports both PostgreSQL and SQLite dialects for testability and portability.
    """
    if df.empty:
        return 0

    df_copy = df.copy()
    if "ingested_at" not in df_copy.columns:
        df_copy["ingested_at"] = datetime.now(UTC)

    # Filter to columns declared on the target table (excluding 'id')
    valid_cols = [c.name for c in table.c if c.name in df_copy.columns and c.name != "id"]
    df_filtered = df_copy[valid_cols]

    records = df_filtered.to_dict(orient="records")
    # Clean NaN/NaT to None for SQL NULL compatibility
    for row in records:
        for k, v in row.items():
            if pd.isna(v):
                row[k] = None

    stmt: Any
    if engine.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt = sqlite_insert(table).values(records)
    else:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(table).values(records)


    update_dict = {
        c.name: stmt.excluded[c.name]
        for c in table.c
        if c.name not in conflict_cols and c.name != "id" and c.name in valid_cols
    }
    stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_dict)

    with engine.begin() as conn:
        conn.execute(stmt)

    return len(records)


def load_weather(df: pd.DataFrame, run_id: int, engine: Engine | None = None) -> int:
    logger.info("Loading weather data", rows=len(df), run_id=run_id)
    eng = engine or get_engine()
    rows = _upsert_dataframe(
        df,
        models.weather_observations,
        eng,
        conflict_cols=["station", "observed_at"],
    )
    logger.info("Weather load finished", rows=rows, run_id=run_id)
    return rows


def load_nse(df: pd.DataFrame, run_id: int, engine: Engine | None = None) -> int:
    logger.info("Loading NSE data", rows=len(df), run_id=run_id)
    eng = engine or get_engine()
    rows = _upsert_dataframe(
        df,
        models.nse_prices,
        eng,
        conflict_cols=["ticker", "trading_date"],
    )
    logger.info("NSE load finished", rows=rows, run_id=run_id)
    return rows


def load_cbk(df: pd.DataFrame, run_id: int, engine: Engine | None = None) -> int:
    logger.info("Loading CBK data", rows=len(df), run_id=run_id)
    eng = engine or get_engine()
    rows = _upsert_dataframe(
        df,
        models.cbk_rates,
        eng,
        conflict_cols=["currency", "rate_date"],
    )
    logger.info("CBK load finished", rows=rows, run_id=run_id)
    return rows

