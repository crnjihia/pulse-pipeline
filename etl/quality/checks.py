# etl/quality/checks.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import Table, func, select
from sqlalchemy.engine import Engine
from structlog import get_logger

from db import models
from db.session import get_engine

logger = get_logger(__name__)


def _record_check(
    engine: Engine,
    run_id: int,
    check_name: str,
    passed: bool,
    details: str | None = None,
) -> None:
    ins = models.dq_results.insert().values(
        run_id=run_id,
        check_name=check_name,
        passed=passed,
        details=details,
        run_at=datetime.now(UTC),
    )
    with engine.begin() as conn:
        conn.execute(ins)


def check_row_count(engine: Engine, table: Table, run_id: int) -> bool:
    stmt = select(func.count()).select_from(table)
    with engine.begin() as conn:
        count = conn.scalar(stmt) or 0
    passed = count > 0
    _record_check(
        engine,
        run_id,
        f"{table.name}_row_count",
        passed,
        None if passed else f"Rows: {count}",
    )
    return passed


def check_freshness(
    engine: Engine,
    table: Table,
    date_column: str,
    max_age_hours: int,
    run_id: int,
) -> bool:
    stmt = select(func.max(getattr(table.c, date_column))).select_from(table)
    with engine.begin() as conn:
        max_date = conn.scalar(stmt)
    details: str | None = None
    passed: bool
    if max_date is None:
        passed = False
        details = "No data"
    else:
        if isinstance(max_date, str):
            max_date = pd.to_datetime(max_date, utc=True).to_pydatetime()
        elif hasattr(max_date, "tzinfo") and max_date.tzinfo is None:
            max_date = max_date.replace(tzinfo=UTC)

        age = datetime.now(UTC) - max_date
        passed = age <= timedelta(hours=max_age_hours)
        details = f"Age: {age}" if not passed else None

    _record_check(engine, run_id, f"{table.name}_freshness", passed, details)
    return passed



def check_duplicates(
    engine: Engine,
    table: Table,
    natural_key: list[str],
    run_id: int,
) -> bool:
    cols = [getattr(table.c, col) for col in natural_key]
    stmt = (
        select(*cols, func.count().label("cnt"))
        .group_by(*cols)
        .having(func.count() > 1)
    )
    with engine.begin() as conn:
        dup_rows = conn.execute(stmt).fetchall()
    passed = len(dup_rows) == 0
    details = f"Duplicates: {len(dup_rows)}" if not passed else None
    _record_check(engine, run_id, f"{table.name}_duplicates", passed, details)
    return passed


def check_not_null(
    engine: Engine,
    table: Table,
    critical_columns: list[str],
    run_id: int,
) -> bool:
    passed = True
    details_parts: list[str] = []
    with engine.begin() as conn:
        for col_name in critical_columns:
            col = getattr(table.c, col_name)
            stmt = select(func.count()).where(col.is_(None)).select_from(table)
            null_count = conn.scalar(stmt) or 0
            if null_count > 0:
                passed = False
                details_parts.append(f"{col_name} nulls={null_count}")
    details = "; ".join(details_parts) if not passed else None
    _record_check(engine, run_id, f"{table.name}_not_null", passed, details)
    return passed


def run_quality_checks(
    pipeline_name: str,
    run_id: int,
    engine: Engine | None = None,
    max_age_hours: int = 26,
) -> bool:
    """
    Executes all quality checks for *pipeline_name*.
    Returns True only if every critical check passes.
    """
    eng = engine or get_engine()
    overall = True

    if pipeline_name == "weather":
        table = models.weather_observations
        overall &= check_row_count(eng, table, run_id)
        overall &= check_freshness(eng, table, "observed_at", max_age_hours, run_id)
        overall &= check_duplicates(eng, table, ["station", "observed_at"], run_id)
        overall &= check_not_null(eng, table, ["station", "observed_at", "temp_c"], run_id)

    elif pipeline_name == "nse":
        table = models.nse_prices
        overall &= check_row_count(eng, table, run_id)
        overall &= check_freshness(eng, table, "trading_date", max_age_hours, run_id)
        overall &= check_duplicates(eng, table, ["ticker", "trading_date"], run_id)
        overall &= check_not_null(eng, table, ["ticker", "trading_date", "close"], run_id)

    elif pipeline_name == "cbk":
        table = models.cbk_rates
        overall &= check_row_count(eng, table, run_id)
        overall &= check_freshness(eng, table, "rate_date", max_age_hours, run_id)
        overall &= check_duplicates(eng, table, ["currency", "rate_date"], run_id)
        overall &= check_not_null(eng, table, ["currency", "rate_date", "buying"], run_id)

    else:
        logger.warning("No quality checks defined for this pipeline", pipeline=pipeline_name)
        return False

    return bool(overall)

