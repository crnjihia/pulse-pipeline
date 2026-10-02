# scheduler/jobs.py
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests
import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from db import models
from db.session import get_engine
from etl.extract import cbk_source, nse_source, weather_source
from etl.load.loader import load_cbk, load_nse, load_weather
from etl.quality.checks import run_quality_checks
from etl.transform.cbk_transform import transform_cbk
from etl.transform.nse_transform import transform_nse
from etl.transform.weather_transform import transform_weather

logger = structlog.get_logger(__name__)


def _create_pipeline_run(pipeline_name: str, started_at: datetime) -> int:
    engine = get_engine()
    ins = models.pipeline_runs.insert().values(
        pipeline_name=pipeline_name,
        started_at=started_at,
        status="running",
        rows_loaded=0,
        error=None,
    )
    with engine.begin() as conn:
        result = conn.execute(ins)
        pk = result.inserted_primary_key
        run_id = int(pk[0]) if pk else 0
    return int(run_id)



def _update_pipeline_run(
    run_id: int,
    finished_at: datetime,
    status: str,
    rows_loaded: int,
    error: str | None = None,
) -> None:
    engine = get_engine()
    upd = (
        models.pipeline_runs.update()
        .where(models.pipeline_runs.c.id == run_id)
        .values(
            finished_at=finished_at,
            status=status,
            rows_loaded=rows_loaded,
            error=error,
        )
    )
    with engine.begin() as conn:
        conn.execute(upd)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=1, max=10),
    reraise=True,
)
def _execute_etl_step(pipeline_name: str, run_id: int) -> int:
    """Execute extract, transform, load, and data quality check with tenacity retry."""
    logger.info("Executing ETL step", pipeline_name=pipeline_name, run_id=run_id)

    if pipeline_name == "weather":
        raw = weather_source.fetch()
        clean = transform_weather(raw)
        rows_loaded = load_weather(clean, run_id)
    elif pipeline_name == "nse":
        raw = nse_source.fetch()
        clean = transform_nse(raw)
        rows_loaded = load_nse(clean, run_id)
    elif pipeline_name == "cbk":
        raw = cbk_source.fetch()
        clean = transform_cbk(raw)
        rows_loaded = load_cbk(clean, run_id)
    else:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    quality_passed = run_quality_checks(pipeline_name, run_id)
    if not quality_passed:
        raise RuntimeError(f"Data quality checks failed for pipeline '{pipeline_name}'")

    return rows_loaded


def _send_failure_webhook(pipeline_name: str, run_id: int, error_msg: str, duration_sec: float) -> None:
    if not settings.WEBHOOK_URL:
        return
    try:
        payload: Any = {
            "text": f"🚨 Hali Pipeline Alert: *{pipeline_name}* run #{run_id} failed after {duration_sec:.1f}s!\nError: {error_msg}",
            "pipeline": pipeline_name,
            "run_id": run_id,
            "status": "failed",
            "duration_sec": duration_sec,
            "error": error_msg,
        }
        requests.post(settings.WEBHOOK_URL, json=payload, timeout=5)
        logger.info("Webhook alert sent successfully", pipeline_name=pipeline_name, run_id=run_id)
    except Exception as webhook_err:
        logger.warning("Failed to dispatch failure webhook", error=str(webhook_err), pipeline_name=pipeline_name)


def run_pipeline(pipeline_name: str) -> int:
    """
    Public entry to execute a pipeline run with tracking, retries, and logging.
    """
    start_time = datetime.now(UTC)
    run_id = _create_pipeline_run(pipeline_name, start_time)
    log = logger.bind(pipeline_name=pipeline_name, run_id=run_id)
    log.info("Pipeline run initiated", started_at=start_time.isoformat())

    rows_loaded = 0
    try:
        rows_loaded = _execute_etl_step(pipeline_name, run_id)
    except Exception as exc:
        finished_time = datetime.now(UTC)
        duration_sec = (finished_time - start_time).total_seconds()
        error_msg = str(exc)
        status = "failed_quality" if "quality checks failed" in error_msg.lower() else "failed"

        _update_pipeline_run(run_id, finished_time, status, rows_loaded, error_msg)
        log.error("Pipeline run failed", status=status, duration_sec=duration_sec, error=error_msg)
        _send_failure_webhook(pipeline_name, run_id, error_msg, duration_sec)
        raise
    else:
        finished_time = datetime.now(UTC)
        duration_sec = (finished_time - start_time).total_seconds()
        status = "success"
        _update_pipeline_run(run_id, finished_time, status, rows_loaded, None)
        log.info(
            "Pipeline run succeeded",
            status=status,
            rows_loaded=rows_loaded,
            duration_sec=duration_sec,
        )
        return rows_loaded


def schedule_jobs() -> BlockingScheduler:
    """Start the APScheduler daemon with configured cron jobs."""
    scheduler = BlockingScheduler(timezone="Africa/Nairobi")

    # Weather: cron hour="*/6" (every 6 hours)
    scheduler.add_job(
        run_pipeline,
        "cron",
        args=["weather"],
        hour="*/6",
        id="weather_job",
        name="Kenya Met Weather Ingestion (Every 6h)",
    )

    # NSE: cron hour=18, minute=0, day_of_week="mon-fri" (18:00 EAT weekdays)
    scheduler.add_job(
        run_pipeline,
        "cron",
        args=["nse"],
        hour=18,
        minute=0,
        day_of_week="mon-fri",
        id="nse_job",
        name="NSE Stock Prices Ingestion (18:00 EAT Mon-Fri)",
    )

    # CBK: cron hour=9, minute=0 (09:00 EAT daily)
    scheduler.add_job(
        run_pipeline,
        "cron",
        args=["cbk"],
        hour=9,
        minute=0,
        id="cbk_job",
        name="CBK Forex Rates Ingestion (09:00 EAT Daily)",
    )

    logger.info("Starting APScheduler BlockingScheduler in Africa/Nairobi timezone")
    scheduler.start()
    return scheduler

