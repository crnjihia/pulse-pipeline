# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from config import settings
from db import models
from db.session import reset_engine


@pytest.fixture(autouse=True)
def sqlite_engine(monkeypatch):
    """Ensure all tests run against an in-memory SQLite database without requiring Postgres."""
    reset_engine()
    test_db_url = "sqlite://"
    monkeypatch.setattr(settings, "DATABASE_URL", test_db_url)
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    models.metadata.create_all(engine)
    monkeypatch.setattr("db.session.get_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr("scheduler.jobs.get_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr("etl.load.loader.get_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr("etl.quality.checks.get_engine", lambda *args, **kwargs: engine)
    yield engine
    reset_engine()

