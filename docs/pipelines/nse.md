# Nairobi Securities Exchange (NSE) Equities Pipeline

The **NSE Equities Pipeline** ingests daily trading sessions from the Nairobi Securities Exchange, standardizing price metrics and calculating daily percentage performance.

## Ingestion Details

* **Identifier**: `nse`
* **Cron Schedule**: Mon–Fri at 18:00 EAT (`0 18 * * 1-5`)
* **Extractor**: `etl/extract/nse_source.py`
* **Transformer**: `etl/transform/nse_transform.py`
* **Destination Table**: `nse_prices`
* **Composite Natural Key**: `(ticker, trading_date)`

---

## Transformation Logic & Metrics

1. **Dash and Null Sanitization**: Missing values represented as `—`, `-`, `null`, `N/A`, or whitespace in trading feeds are converted to `np.nan`.
2. **Numeric Coercion**: Columns (`open`, `high`, `low`, `close`, `volume`, `previous`) are cast to floating point numbers.
3. **Daily Change Calculation**:
   $$\text{Baseline} = \text{open if open} > 0 \text{ else previous}$$
   $$\text{daily\_change\_pct} = \frac{\text{close} - \text{Baseline}}{\text{Baseline}} \times 100$$
4. **Deduplication**: Rows with duplicate `(ticker, trading_date)` keys are dropped.

---

## Data Schema: `nse_prices`

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key | Sequence identifier |
| `ticker` | `VARCHAR` | No | Natural Key | Stock ticker symbol (e.g. `SCOM`, `EQTY`, `KCB`) |
| `trading_date` | `TIMESTAMPTZ` | No | Natural Key | Trading session date in UTC |
| `open` | `FLOAT` | Yes | - | Opening price in KES |
| `high` | `FLOAT` | Yes | - | Session high in KES |
| `low` | `FLOAT` | Yes | - | Session low in KES |
| `close` | `FLOAT` | Yes | - | Closing price in KES |
| `volume` | `FLOAT` | Yes | - | Traded volume |
| `daily_change_pct` | `FLOAT` | Yes | - | Daily percentage change |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Timestamp when loaded into DB |
