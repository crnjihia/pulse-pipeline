# dashboard/app.py
from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db.session import get_engine

st.set_page_config(
    page_title="Hali Pipeline Dashboard",
    page_icon="🇰🇪",
    layout="wide",
)


def format_time_ago(dt: datetime | pd.Timestamp | None) -> str:
    """Returns human-friendly relative time (e.g. '2h ago')."""
    if dt is None or pd.isna(dt):
        return "never"
    ts = pd.to_datetime(dt, utc=True).to_pydatetime()
    diff = datetime.now(UTC) - ts
    seconds = max(0, int(diff.total_seconds()))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


@st.cache_data(ttl=60)
def load_table(table_name: str) -> pd.DataFrame:
    try:
        engine = get_engine()
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql_query(query, engine)
    except Exception as exc:
        st.warning(f"Unable to read table {table_name}: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def get_recent_runs() -> pd.DataFrame:
    try:
        engine = get_engine()
        query = "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 10"
        return pd.read_sql_query(query, engine)
    except Exception:
        return pd.DataFrame()


# -------------------------------------------------
# Header & Data Freshness
# -------------------------------------------------
st.title("🇰🇪 Hali Pipeline — Kenyan Public Data ETL")

recent_runs = get_recent_runs()
if not recent_runs.empty:
    last_finished = recent_runs["finished_at"].dropna().iloc[0] if not recent_runs["finished_at"].dropna().empty else None
    st.markdown(f"**Data Freshness:** Last updated: {format_time_ago(last_finished)}")
else:
    st.markdown("**Data Freshness:** No pipeline runs recorded yet")

# -------------------------------------------------
# Sidebar: Pipeline Health
# -------------------------------------------------
st.sidebar.title("Pipeline Health")
st.sidebar.caption("Last 10 pipeline executions")

if not recent_runs.empty:
    health_df = recent_runs.copy()
    health_df["started_at"] = pd.to_datetime(health_df["started_at"], utc=True)
    health_df["finished_at"] = pd.to_datetime(health_df["finished_at"], utc=True)
    health_df["duration"] = (
        (health_df["finished_at"] - health_df["started_at"]).dt.total_seconds().apply(
            lambda s: f"{s:.1f}s" if pd.notna(s) else "running"
        )
    )
    display_cols = ["pipeline_name", "status", "duration", "rows_loaded"]
    st.sidebar.dataframe(health_df[display_cols], hide_index=True, use_container_width=True)
else:
    st.sidebar.info("No runs logged yet.")

# -------------------------------------------------
# Main Tabs
# -------------------------------------------------
tab_weather, tab_nse, tab_forex = st.tabs(["🌤️ Weather", "📈 NSE Stocks", "💱 Forex Rates"])

# -------------------------------------------------
# Tab 1: Weather
# -------------------------------------------------
with tab_weather:
    st.subheader("Kenya Meteorological Department — Observations")
    df_weather = load_table("weather_observations")

    if df_weather.empty:
        st.info("No weather data found in database. Run `python -m hali run --pipeline weather` to ingest data.")
    else:
        df_weather["observed_at"] = pd.to_datetime(df_weather["observed_at"], utc=True)
        stations = sorted(df_weather["station"].dropna().unique().tolist())
        selected_station = st.selectbox("Select Station", stations)

        station_df = df_weather[df_weather["station"] == selected_station].sort_values("observed_at")

        latest_weather = station_df.iloc[-1]
        col1, col2, col3 = st.columns(3)
        col1.metric("Latest Temperature", f"{latest_weather['temp_c']} °C")
        col2.metric("Latest Rainfall", f"{latest_weather['rainfall_mm']} mm")
        col3.metric("Latest Humidity", f"{latest_weather['humidity_pct']} %")

        fig_temp = px.line(
            station_df,
            x="observed_at",
            y="temp_c",
            markers=True,
            title=f"Temperature Over Time — {selected_station}",
            labels={"observed_at": "Time (UTC)", "temp_c": "Temperature (°C)"},
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_rain = px.bar(
            station_df,
            x="observed_at",
            y="rainfall_mm",
            title=f"Precipitation (mm) — {selected_station}",
            labels={"observed_at": "Time (UTC)", "rainfall_mm": "Rainfall (mm)"},
        )
        st.plotly_chart(fig_rain, use_container_width=True)

# -------------------------------------------------
# Tab 2: NSE
# -------------------------------------------------
with tab_nse:
    st.subheader("Nairobi Securities Exchange (NSE) — Daily Equities")
    df_nse = load_table("nse_prices")

    if df_nse.empty:
        st.info("No NSE stock data found. Run `python -m hali run --pipeline nse` to ingest data.")
    else:
        df_nse["trading_date"] = pd.to_datetime(df_nse["trading_date"], utc=True)
        tickers = sorted(df_nse["ticker"].dropna().unique().tolist())
        selected_ticker = st.selectbox("Select Ticker", tickers)

        ticker_df = df_nse[df_nse["ticker"] == selected_ticker].sort_values("trading_date")

        min_d = ticker_df["trading_date"].min().date()
        max_d = ticker_df["trading_date"].max().date()

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("From Date", value=min_d, min_value=min_d, max_value=max_d)
        with date_col2:
            end_date = st.date_input("To Date", value=max_d, min_value=min_d, max_value=max_d)

        mask = (ticker_df["trading_date"].dt.date >= start_date) & (ticker_df["trading_date"].dt.date <= end_date)
        filtered_nse = ticker_df.loc[mask]

        if not filtered_nse.empty:
            latest_stock = filtered_nse.iloc[-1]
            change = latest_stock.get("daily_change_pct", 0.0)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Close Price", f"KES {latest_stock['close']:.2f}")
            col2.metric("Daily Change", f"{change:+.2f}%" if pd.notna(change) else "N/A")
            col3.metric("High", f"KES {latest_stock['high']:.2f}" if pd.notna(latest_stock['high']) else "N/A")
            col4.metric("Volume", f"{int(latest_stock['volume']):,}" if pd.notna(latest_stock['volume']) else "N/A")

            # Candlestick or line
            has_ohlc = filtered_nse[["open", "high", "low", "close"]].notna().all(axis=1).any()
            if has_ohlc:
                fig_candle = go.Figure(
                    data=[
                        go.Candlestick(
                            x=filtered_nse["trading_date"],
                            open=filtered_nse["open"],
                            high=filtered_nse["high"],
                            low=filtered_nse["low"],
                            close=filtered_nse["close"],
                            name="OHLC",
                        )
                    ]
                )
                fig_candle.update_layout(
                    title=f"{selected_ticker} Candlestick Chart",
                    xaxis_title="Trading Date",
                    yaxis_title="Price (KES)",
                )
                st.plotly_chart(fig_candle, use_container_width=True)
            else:
                fig_line = px.line(
                    filtered_nse,
                    x="trading_date",
                    y="close",
                    title=f"{selected_ticker} Close Price Over Time",
                    markers=True,
                )
                st.plotly_chart(fig_line, use_container_width=True)

            fig_vol = px.bar(
                filtered_nse,
                x="trading_date",
                y="volume",
                title=f"{selected_ticker} Trading Volume",
                labels={"trading_date": "Trading Date", "volume": "Volume"},
            )
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.warning("No data found for the selected date window.")

# -------------------------------------------------
# Tab 3: Forex
# -------------------------------------------------
with tab_forex:
    st.subheader("Central Bank of Kenya (CBK) — Official Forex Rates")
    df_cbk = load_table("cbk_rates")

    if df_cbk.empty:
        st.info("No forex rates found. Run `python -m hali run --pipeline cbk` to ingest data.")
    else:
        df_cbk["rate_date"] = pd.to_datetime(df_cbk["rate_date"], utc=True)
        all_currencies = sorted(df_cbk["currency"].dropna().unique().tolist())
        default_currencies = [c for c in ["USD", "EUR", "GBP"] if c in all_currencies] or all_currencies[:3]

        selected_currencies = st.multiselect(
            "Select Currencies to compare against KES",
            options=all_currencies,
            default=default_currencies,
        )

        filtered_cbk = df_cbk[df_cbk["currency"].isin(selected_currencies)].sort_values("rate_date")

        if not filtered_cbk.empty:
            metric_cols = st.columns(min(4, len(selected_currencies)))
            for idx, curr in enumerate(selected_currencies[:4]):
                curr_latest = filtered_cbk[filtered_cbk["currency"] == curr].iloc[-1]
                metric_cols[idx % len(metric_cols)].metric(
                    f"{curr} / KES",
                    f"{curr_latest['mean']:.2f}",
                    help=f"Buying: {curr_latest['buying']:.2f} | Selling: {curr_latest['selling']:.2f}",
                )

            fig_forex = px.line(
                filtered_cbk,
                x="rate_date",
                y="mean",
                color="currency",
                markers=True,
                title="Official CBK Mean Exchange Rates (KES per Foreign Currency)",
                labels={"rate_date": "Date", "mean": "Mean Rate (KES)", "currency": "Currency"},
            )
            st.plotly_chart(fig_forex, use_container_width=True)
        else:
            st.warning("Please select at least one currency.")

