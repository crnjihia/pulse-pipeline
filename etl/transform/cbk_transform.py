# etl/transform/cbk_transform.py
from __future__ import annotations

import pandas as pd
from structlog import get_logger

logger = get_logger(__name__)

CBK_SCHEMA = ["currency", "rate_date", "buying", "selling", "mean"]


def transform_cbk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans Central Bank of Kenya forex data (pure function: DataFrame in -> DataFrame out).
    Schema:
        - currency (str): 3-letter currency code (e.g., USD, EUR, GBP)
        - rate_date (datetime UTC): Date of official published rates
        - buying (float): Bank buying rate against KES
        - selling (float): Bank selling rate against KES
        - mean (float): Official central mean rate against KES
    """
    logger.info("Starting CBK transform", rows=len(df))
    df = df.copy()

    # Support raw column named 'date' or 'rate_date'
    if "date" in df.columns and "rate_date" not in df.columns:
        df["rate_date"] = df["date"]

    required = {"currency", "rate_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for CBK transform: {missing}")

    numeric_cols = ["buying", "selling", "mean"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        else:
            df[col] = float("nan")

    df["rate_date"] = pd.to_datetime(df["rate_date"], utc=True, errors="coerce")
    df = df.dropna(subset=["currency", "rate_date"])
    df = df.drop_duplicates(subset=["currency", "rate_date"])
    df = df.sort_values(["rate_date", "currency"]).reset_index(drop=True)

    result = df[CBK_SCHEMA]
    logger.info("CBK transform complete", rows=len(result))
    return result


transform = transform_cbk

