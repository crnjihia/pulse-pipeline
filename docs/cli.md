# CLI & Scheduler Reference

Pulse Pipeline includes a CLI module (`cli.py`) and a background daemon (`scheduler/jobs.py`) powered by APScheduler.

---

## Command Line Interface (CLI)

You can invoke the CLI using `python -m pulse` (or the alias `python -m hali`):

```text
usage: python -m pulse [-h] {run,schedule,dashboard} ...

Pulse Pipeline – Automated ETL for Kenyan Public Data

options:
  -h, --help            show this help message and exit

subcommands:
  {run,schedule,dashboard}
    run                 Execute a pipeline once
    schedule            Start the APScheduler daemon
    dashboard           Launch the Streamlit analytics dashboard
```

### 1. `run` Subcommand

Executes a single or composite pipeline run on demand:

```bash
# Run all three pipelines
python -m pulse run --pipeline all

# Run individual pipeline
python -m pulse run --pipeline weather
python -m pulse run --pipeline nse
python -m pulse run --pipeline cbk
```

### 2. `schedule` Subcommand

Starts the blocking APScheduler daemon to run pipelines continuously on configured cron schedules:

```bash
python -m pulse schedule
```

### 3. `dashboard` Subcommand

Spawns the Streamlit dashboard server on port 8501:

```bash
python -m pulse dashboard
```

---

## Scheduler Configuration

The scheduler daemon runs in the **`Africa/Nairobi` (EAT / UTC+3)** timezone:

| Job Name | Cron Expression | Timing Description |
|:---|:---|:---|
| **Weather Ingestion** | `0 */6 * * *` | Every 6 hours on the hour |
| **NSE Stock Prices** | `0 18 * * 1-5` | Monday through Friday at 18:00 EAT |
| **CBK Forex Rates** | `0 9 * * *` | Daily at 09:00 EAT |

---

## Webhook Alerts

Configure the `WEBHOOK_URL` in your `.env` file to receive automated failure alerts:

```ini
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

When an ETL run fails (due to network failure after retries, or data quality assertions), a payload is dispatched containing:
- Pipeline name
- Run identifier
- Failure reason / exception message
- Total execution duration in seconds
