# tests/test_scheduler_and_cli.py
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from cli import main as cli_main
from config import settings
from dashboard.app import format_time_ago
from db import models
from scheduler.jobs import run_pipeline


@pytest.fixture(autouse=True)
def mock_offline(monkeypatch):
    monkeypatch.setattr("requests.get", lambda *a, **kw: (_ for _ in ()).throw(Exception("Offline")))



def test_run_pipeline_weather(sqlite_engine, monkeypatch):
    # Mock quality checks to pass on sample fixture data
    monkeypatch.setattr("scheduler.jobs.run_quality_checks", lambda name, run_id: True)

    rows = run_pipeline("weather")
    assert rows > 0

    with sqlite_engine.begin() as conn:
        runs = conn.execute(models.pipeline_runs.select()).fetchall()
        assert len(runs) == 1
        assert runs[0].pipeline_name == "weather"
        assert runs[0].status == "success"
        assert runs[0].rows_loaded == rows


def test_run_pipeline_nse(sqlite_engine, monkeypatch):
    monkeypatch.setattr("scheduler.jobs.run_quality_checks", lambda name, run_id: True)

    rows = run_pipeline("nse")
    assert rows > 0

    with sqlite_engine.begin() as conn:
        runs = conn.execute(models.pipeline_runs.select().where(models.pipeline_runs.c.pipeline_name == "nse")).fetchall()
        assert len(runs) == 1
        assert runs[0].status == "success"


def test_run_pipeline_cbk(sqlite_engine, monkeypatch):
    monkeypatch.setattr("scheduler.jobs.run_quality_checks", lambda name, run_id: True)

    rows = run_pipeline("cbk")
    assert rows > 0

    with sqlite_engine.begin() as conn:
        runs = conn.execute(models.pipeline_runs.select().where(models.pipeline_runs.c.pipeline_name == "cbk")).fetchall()
        assert len(runs) == 1
        assert runs[0].status == "success"


def test_run_pipeline_quality_failure_and_webhook(sqlite_engine, monkeypatch):
    monkeypatch.setattr("scheduler.jobs.run_quality_checks", lambda name, run_id: False)
    monkeypatch.setattr(settings, "WEBHOOK_URL", "https://hooks.slack.com/services/mock/alert")

    webhook_called = []

    def mock_post(url, json=None, timeout=None):
        webhook_called.append((url, json))

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(RuntimeError, match="Data quality checks failed"):
        run_pipeline("weather")

    assert len(webhook_called) == 1
    assert webhook_called[0][1]["status"] == "failed"

    with sqlite_engine.begin() as conn:
        runs = conn.execute(models.pipeline_runs.select()).fetchall()
        assert runs[-1].status == "failed_quality"


def test_cli_run_single_and_all(sqlite_engine, monkeypatch):
    monkeypatch.setattr("scheduler.jobs.run_quality_checks", lambda name, run_id: True)

    # CLI run weather
    cli_main(["run", "--pipeline", "weather"])
    # CLI run all
    cli_main(["run", "--pipeline", "all"])

    with sqlite_engine.begin() as conn:
        runs = conn.execute(models.pipeline_runs.select()).fetchall()
        # 1 from weather + 3 from all (weather, nse, cbk) = 4 total
        assert len(runs) == 4


def test_cli_help(capsys):
    with pytest.raises(SystemExit):
        cli_main(["--help"])


def test_cli_schedule_and_dashboard(monkeypatch):
    schedule_called = []
    subprocess_called = []

    monkeypatch.setattr("cli.schedule_jobs", lambda: schedule_called.append(True))
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: subprocess_called.append(a))

    cli_main(["schedule"])
    assert len(schedule_called) == 1

    cli_main(["dashboard"])
    assert len(subprocess_called) == 1


def test_cli_no_args_prints_help(capsys):
    cli_main([])
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "usage:" in captured.err.lower() or "help" in captured.out.lower()


def test_dashboard_helpers(sqlite_engine):
    from dashboard.app import get_recent_runs, load_table

    # Test load_table
    df_w = load_table("weather_observations")
    assert isinstance(df_w, pd.DataFrame)

    # Test get_recent_runs
    df_runs = get_recent_runs()
    assert isinstance(df_runs, pd.DataFrame)


def test_db_session_reset(sqlite_engine):
    from db.session import get_engine, reset_engine

    eng = get_engine()
    assert eng is not None
    reset_engine()


def test_quality_checks_unknown_pipeline(sqlite_engine):
    from etl.quality.checks import run_quality_checks

    passed = run_quality_checks("non_existent_pipeline", run_id=99, engine=sqlite_engine)
    assert passed is False


def test_dashboard_format_time_ago():
    now = datetime.now(UTC)
    assert format_time_ago(None) == "never"
    assert format_time_ago(now - timedelta(seconds=10)) == "just now"
    assert format_time_ago(now - timedelta(minutes=5)) == "5m ago"
    assert format_time_ago(now - timedelta(hours=3)) == "3h ago"
    assert format_time_ago(now - timedelta(days=2)) == "2d ago"

