# Analytics Dashboard

Pulse Pipeline provides a dark-themed **Streamlit + Plotly** operational analytics dashboard located in `dashboard/app.py`.

---

## Launching the Dashboard

```bash
# Launch via CLI shortcut
python -m pulse dashboard

# Or run directly with Streamlit
streamlit run dashboard/app.py
```
By default, the server listens at **http://localhost:8501**.

---

## Key Dashboard Views

### 1. Header & Data Freshness
* Real-time temporal latency indicator comparing current UTC time against the most recently completed pipeline execution.
* Displays relative human-friendly time (e.g. `12m ago`, `2h ago`).

### 2. Operational Health Sidebar
* Tracks the last 10 pipeline executions across all jobs.
* Surfaces outcome status (`success`, `running`, `failed_quality`, `failed`), execution duration in seconds, and number of rows loaded.

### 3. Weather Tab
* **Station Selector**: Filter telemetry across stations (e.g., `NairobiHQ`, `MombasaAirport`).
* **KPI Metrics**: Cards displaying latest Temperature (°C), Rainfall (mm), and Relative Humidity (%).
* **Interactive Time-Series**: Plotly line chart of temperatures and precipitation bar chart.

### 4. NSE Equities Tab
* **Ticker Selector & Date Range Filter**: Select any tracked stock symbol (e.g. `SCOM`, `EQTY`) and adjust observation windows.
* **Candlestick / OHLC Chart**: Visualizes Open, High, Low, and Close price action.
* **Volume Bars**: Daily trading volume distribution.

### 5. CBK Forex Tab
* **Currency Selector**: Multi-select comparing foreign currencies against KES.
* **Spread Cards**: Live buying, selling, and mean spread metrics.
* **Exchange Rate History**: Interactive Plotly multi-line chart tracking historical currency valuation against KES.
