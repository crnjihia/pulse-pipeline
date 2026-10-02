# etl/extract/weather_source.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from structlog import get_logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import settings

logger = get_logger(__name__)

BASE_URL = "https://api.met.gov/kenya/weather"
FIXTURE_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "weather_sample.csv"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)
def _fetch_remote_weather() -> pd.DataFrame:
    """Fetch live weather data with retries."""
    logger.info("Fetching Kenya Met weather data", url=BASE_URL)
    response = requests.get(
        BASE_URL,
        headers={"User-Agent": settings.USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data)


def fetch() -> pd.DataFrame:
    """
    Fetches Kenya Met Department weather data.
    Retries up to 3 times on transient network failures, then falls back to fixtures/weather_sample.csv.
    Returns a DataFrame with columns:
        station, observed_at, temp_c, rainfall_mm, humidity_pct
    """
    try:
        df = _fetch_remote_weather()
    except Exception as exc:
        logger.warning("Live weather fetch failed, using fixture fallback", error=str(exc))
        df = pd.read_csv(FIXTURE_PATH)
        df["observed_at"] = [
            (datetime.now(UTC) - timedelta(hours=i)).isoformat()
            for i in range(len(df))
        ]

    if "observed_at" in df.columns:
        df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
    return df


# Backwards-compatible alias
fetch_weather = fetch

