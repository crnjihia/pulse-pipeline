# tests/test_transform.py
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from etl.transform.cbk_transform import CBK_SCHEMA, transform_cbk
from etl.transform.nse_transform import NSE_SCHEMA, transform_nse
from etl.transform.weather_transform import WEATHER_SCHEMA, transform_weather

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# -------------------------------------------------------------
# (c) Unit Tests Using Fixture CSVs
# -------------------------------------------------------------
def test_weather_transform_using_fixture():
    fixture_path = FIXTURES_DIR / "weather_sample.csv"
    assert fixture_path.exists()

    df_raw = pd.read_csv(fixture_path)
    df_raw_copy = df_raw.copy()

    df_clean = transform_weather(df_raw)

    # Pure function check: input df not mutated
    pd.testing.assert_frame_equal(df_raw, df_raw_copy)

    # Schema check
    assert list(df_clean.columns) == WEATHER_SCHEMA
    assert len(df_clean) == len(df_raw)
    assert pd.api.types.is_datetime64_any_dtype(df_clean["observed_at"])
    assert df_clean["temp_c"].dtype == float
    assert df_clean["rainfall_mm"].dtype == float
    assert df_clean["humidity_pct"].dtype == float
    assert df_clean["is_outlier"].dtype == bool


def test_nse_transform_using_fixture():
    fixture_path = FIXTURES_DIR / "nse_sample.csv"
    assert fixture_path.exists()

    df_raw = pd.read_csv(fixture_path)
    df_raw_copy = df_raw.copy()

    df_clean = transform_nse(df_raw)

    # Pure function check
    pd.testing.assert_frame_equal(df_raw, df_raw_copy)

    # Schema check
    assert list(df_clean.columns) == NSE_SCHEMA
    assert len(df_clean) == 2
    assert pd.api.types.is_datetime64_any_dtype(df_clean["trading_date"])
    assert df_clean["close"].dtype == float
    assert df_clean["daily_change_pct"].dtype == float

    # Verify "—" was correctly handled as NaN
    xyz_row = df_clean[df_clean["ticker"] == "XYZ"].iloc[0]
    assert np.isnan(xyz_row["open"])
    # Daily change fell back to previous (20) -> (21 - 20) / 20 * 100 = 5.0%
    assert np.isclose(xyz_row["daily_change_pct"], 5.0)


def test_cbk_transform_using_fixture():
    fixture_path = FIXTURES_DIR / "cbk_sample.csv"
    assert fixture_path.exists()

    df_raw = pd.read_csv(fixture_path)
    df_raw_copy = df_raw.copy()

    df_clean = transform_cbk(df_raw)

    # Pure function check
    pd.testing.assert_frame_equal(df_raw, df_raw_copy)

    # Schema check
    assert list(df_clean.columns) == CBK_SCHEMA
    assert len(df_clean) == 3
    assert pd.api.types.is_datetime64_any_dtype(df_clean["rate_date"])
    assert df_clean["buying"].dtype == float
    assert df_clean["selling"].dtype == float
    assert df_clean["mean"].dtype == float


# -------------------------------------------------------------
# Additional Edge Case & Resilience Tests
# -------------------------------------------------------------
def test_weather_transform_deduplication_and_outliers():
    df_raw = pd.DataFrame(
        {
            "station": ["A", "A", "B", "C", "D", "E", "F"],
            "observed_at": [
                "2023-01-01T00:00:00Z",
                "2023-01-01T00:00:00Z",  # duplicate key
                "2023-01-01T01:00:00Z",
                "2023-01-01T02:00:00Z",
                "2023-01-01T03:00:00Z",
                "2023-01-01T04:00:00Z",
                "2023-01-01T05:00:00Z",
            ],
            "temp_c": [20.0, 20.0, 21.0, 22.0, 21.5, 20.5, 95.0],  # 95 is clear outlier
            "rainfall_mm": [0, 0, 0, 0, 0, 0, 0],
            "humidity_pct": [60, 60, 62, 63, 61, 64, 60],
        }
    )
    df = transform_weather(df_raw)
    assert len(df) == 6
    outliers = df[df["is_outlier"]]
    assert len(outliers) == 1
    assert outliers.iloc[0]["station"] == "F"


def test_weather_transform_missing_columns():
    with pytest.raises(ValueError, match="Missing columns"):
        transform_weather(pd.DataFrame({"station": ["A"]}))


def test_nse_transform_drops_missing_close():
    df_raw = pd.DataFrame(
        {
            "ticker": ["VALID", "NOCLOSE"],
            "date": ["2023-01-01", "2023-01-01"],
            "open": ["10", "15"],
            "close": ["12", np.nan],
        }
    )
    df = transform_nse(df_raw)
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "VALID"


def test_cbk_transform_date_renaming_and_deduplication():
    df_raw = pd.DataFrame(
        {
            "currency": ["USD", "USD"],
            "date": ["2023-01-01", "2023-01-01"],  # uses 'date' instead of 'rate_date'
            "buying": ["130", "130"],
            "selling": ["131", "131"],
            "mean": ["130.5", "130.5"],
        }
    )
    df = transform_cbk(df_raw)
    assert len(df) == 1
    assert "rate_date" in df.columns
    assert df["buying"].iloc[0] == 130.0

