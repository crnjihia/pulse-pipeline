# tests/test_extract.py
import pandas as pd
import requests

from etl.extract import cbk_source, nse_source, weather_source


def _raise_request_exception(*_args, **_kwargs):
    raise requests.RequestException("Simulated upstream timeout")


def test_fetch_weather_fallback(monkeypatch):
    monkeypatch.setattr("requests.get", _raise_request_exception)
    df = weather_source.fetch()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    for col in ["station", "observed_at", "temp_c"]:
        assert col in df.columns
    # Ensure backwards-compatible alias also works
    assert len(weather_source.fetch_weather()) == len(df)


def test_fetch_weather_success(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "station": "LiveStation",
                    "observed_at": "2026-10-01T00:00:00Z",
                    "temp_c": 22.0,
                    "rainfall_mm": 1.2,
                    "humidity_pct": 65.0,
                }
            ]

    monkeypatch.setattr("requests.get", lambda *a, **kw: DummyResponse())
    df = weather_source.fetch()
    assert len(df) == 1
    assert df["station"].iloc[0] == "LiveStation"


def test_fetch_nse_fallback(monkeypatch):
    monkeypatch.setattr("requests.get", _raise_request_exception)
    df = nse_source.fetch()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    for col in ["ticker", "name", "open", "high", "low", "close", "volume", "date"]:
        assert col in df.columns
    assert len(nse_source.fetch_nse()) == len(df)


def test_fetch_nse_success(monkeypatch):
    csv_payload = "ticker,name,previous,open,high,low,close,volume,date\nSAF,Safaricom,15,15,16,14,15.5,5000,2026-10-01\n"

    class DummyResponse:
        text = csv_payload

        def raise_for_status(self):
            pass

    monkeypatch.setattr("requests.get", lambda *a, **kw: DummyResponse())
    df = nse_source.fetch()
    assert len(df) == 1
    assert df["ticker"].iloc[0] == "SAF"


def test_fetch_cbk_fallback(monkeypatch):
    monkeypatch.setattr("requests.get", _raise_request_exception)
    df = cbk_source.fetch()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    for col in ["currency", "buying", "selling", "mean", "rate_date"]:
        assert col in df.columns
    assert len(cbk_source.fetch_cbk()) == len(df)


def test_fetch_cbk_success(monkeypatch):
    csv_payload = "currency,buying,selling,mean,date\nUSD,129.50,130.50,130.00,2026-10-01\n"

    class DummyResponse:
        text = csv_payload

        def raise_for_status(self):
            pass

    monkeypatch.setattr("requests.get", lambda *a, **kw: DummyResponse())
    df = cbk_source.fetch()
    assert len(df) == 1
    assert df["currency"].iloc[0] == "USD"

