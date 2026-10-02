# etl/transform/nse_transform.py
from __future__ import annotations

import numpy as np
import pandas as pd
from structlog import get_logger

logger = get_logger(__name__)

NSE_SCHEMA = [
    "ticker",
    "trading_date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "daily_change_pct",
]


def transform_nse(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans NSE price data (pure function: DataFrame in -> DataFrame out).
    Schema:
        - ticker (str): Stock ticker symbol
        - trading_date (datetime UTC): Date/time of trading session
        - open (float): Opening price
        - high (float): Session high
        - low (float): Session low
        - close (float): Closing price
        - volume (float): Number of shares traded
        - daily_change_pct (float): Daily percentage change
    """
    logger.info("Starting NSE transform", rows=len(df))
    df = df.copy()

    # Normalize date column if named 'date'
    if "date" in df.columns and "trading_date" not in df.columns:
        df["trading_date"] = df["date"]

    required = {"ticker", "close", "trading_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing critical columns for NSE transform: {missing}")

    # Standardize empty/dash representations
    df = df.replace(["—", "-", "N/A", "null", ""], np.nan)

    numeric_cols = ["previous", "open", "high", "low", "close", "volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)
        else:
            df[col] = np.nan

    df["trading_date"] = pd.to_datetime(df["trading_date"], utc=True, errors="coerce")

    # Drop rows missing critical close or trading_date
    df = df.dropna(subset=["close", "trading_date"])

    # Compute daily_change_pct: compare close with open (or fallback to previous)
    baseline = df["open"].where(df["open"].notna() & (df["open"] != 0), df["previous"])
    df["daily_change_pct"] = np.where(
        baseline.notna() & (baseline != 0),
        ((df["close"] - baseline) / baseline) * 100.0,
        np.nan,
    )

    df = df.drop_duplicates(subset=["ticker", "trading_date"])
    df = df.sort_values(["trading_date", "ticker"]).reset_index(drop=True)

    result = df[NSE_SCHEMA]
    logger.info("NSE transform complete", rows=len(result))
    return result


transform = transform_nse

