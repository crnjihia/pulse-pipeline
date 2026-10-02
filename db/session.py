# db/session.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import settings
from db import models

_engine: Engine | None = None
_engine_url: str | None = None


def get_engine(url: str | None = None) -> Engine:
    """Returns a singleton SQLAlchemy engine, re-initializing if the URL changes."""
    global _engine, _engine_url
    target_url = url or settings.DATABASE_URL
    if _engine is None or _engine_url != target_url:
        _engine = create_engine(target_url, future=True, echo=False)
        _engine_url = target_url
        models.metadata.create_all(_engine)
    return _engine


def reset_engine() -> None:
    """Clears cached engine (useful for test isolation)."""
    global _engine, _engine_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_url = None

