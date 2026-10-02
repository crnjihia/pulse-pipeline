# etl/transform/weather_transform.py
from __future__ import annotations

import pandas as pd
from structlog import get_logger

logger = get_logger(__name__)

WEATHER_SCHEMA = [
    "station",
    "observed_at",
    "temp_c",
    "rainfall_mm",
    "humidity_pct",
    "is_outlier",
]


def transform_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans weather observations (pure function: DataFrame in -> DataFrame out).
    Schema:
        - station (str): Weather station identifier
        - observed_at (datetime UTC): Timestamp of observation
        - temp_c (float): Temperature in degrees Celsius
        - rainfall_mm (float): Precipitation in millimeters
        - humidity_pct (float): Relative humidity percentage
        - is_outlier (bool): True if flagged as IQR outlier on numeric fields
    """
    logger.info("Starting weather transform", rows=len(df))
    required = {"station", "observed_at", "temp_c", "rainfall_mm", "humidity_pct"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for weather transform: {missing}")

    df = df.copy()
    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")

    numeric_cols = ["temp_c", "rainfall_mm", "humidity_pct"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float)

    # Outlier detection (IQR) per numeric column
    outlier_mask = pd.Series(False, index=df.index)
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) >= 4:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                mask = df[col].notna() & ((df[col] < lower) | (df[col] > upper))
                outlier_mask = outlier_mask | mask

    df["is_outlier"] = outlier_mask.astype(bool)
    df = df.drop_duplicates(subset=["station", "observed_at"]).reset_index(drop=True)

    result = df[WEATHER_SCHEMA]
    logger.info(
        "Weather transform complete",
        rows=len(result),
        outliers=int(result["is_outlier"].sum()),
    )
    return result


transform = transform_weather

