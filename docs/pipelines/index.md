# Data Pipelines Overview

Pulse Pipeline manages three domain pipelines that extract, clean, and persist public data.

| Pipeline | Source | Cron Schedule (EAT) | Target Table | Composite Key |
|:---|:---|:---|:---|:---|
| **[Kenya Met Weather](weather.md)** | Kenya Meteorological Dept | Every 6 hours (`0 */6 * * *`) | `weather_observations` | `(station, observed_at)` |
| **[NSE Equities](nse.md)** | Nairobi Securities Exchange | Mon–Fri at 18:00 (`0 18 * * 1-5`) | `nse_prices` | `(ticker, trading_date)` |
| **[CBK Forex](cbk.md)** | Central Bank of Kenya | Daily at 09:00 (`0 9 * * *`) | `cbk_rates` | `(currency, rate_date)` |

---

## Executing Pipelines Manually

You can execute all pipelines or any specific pipeline on demand via the CLI:

```bash
# Ingest all three pipelines sequentially
python -m pulse run --pipeline all

# Run individual pipelines
python -m pulse run --pipeline weather
python -m pulse run --pipeline nse
python -m pulse run --pipeline cbk
```

Each run:
1. Generates a new entry in `pipeline_runs` with status `running`.
2. Fetches upstream data with automatic retries and fixture fallback.
3. Applies pure transformations and outlier detection.
4. Performs an idempotent upsert into the destination table.
5. Runs data quality assertions and records checks in `dq_results`.
6. Updates `pipeline_runs` with final outcome (`success` or `failed_quality`) and execution duration.
7. Dispatches webhook notifications on failure.
