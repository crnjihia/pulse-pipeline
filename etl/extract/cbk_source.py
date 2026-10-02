# etl/extract/cbk_source.py
from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from structlog import get_logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import settings

logger = get_logger(__name__)

BASE_URL = "https://www.cbk.go.ke/forex-rates"
FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "cbk_sample.csv"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _fetch_remote_cbk() -> pd.DataFrame:
    """Fetch live CBK forex rates with retries."""
    logger.info("Fetching CBK forex rate data", url=BASE_URL)
    response = requests.get(
        BASE_URL,
        headers={"User-Agent": settings.USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    return pd.read_csv(io.StringIO(response.text))


def fetch() -> pd.DataFrame:
    """
    Fetches Central Bank of Kenya forex rates.
    Retries up to 3 times on transient network failures, then falls back to fixtures/cbk_sample.csv.
    Expected raw columns:
        currency, buying, selling, mean, date (or rate_date)
    """
    try:
        df = _fetch_remote_cbk()
    except Exception as exc:
        logger.warning("Live CBK fetch failed, using fixture fallback", error=str(exc))
        df = pd.read_csv(FIXTURE_PATH)
        df["rate_date"] = datetime.now(UTC).strftime("%Y-%m-%d")
    return df


# Backwards-compatible alias
fetch_cbk = fetch

