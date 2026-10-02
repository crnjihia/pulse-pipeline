# 🇰🇪 Hali Pipeline — Kenyan Public Data ETL & Analytics

[![CI](https://github.com/yourorg/hali-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/hali-pipeline/actions)
[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen)](https://github.com/yourorg/hali-pipeline)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Hali Pipeline** is an automated, production-grade ETL system and real-time observability platform that ingests, cleans, validates, and serves key Kenyan public datasets:
> - **Kenya Meteorological Department**: Observational weather telemetry (temperature, rainfall, humidity, IQR statistical outliers).
> - **Nairobi Securities Exchange (NSE)**: Daily equity trading prices (open, high, low, close, volume, daily percentage change).
> - **Central Bank of Kenya (CBK)**: Official daily foreign exchange rates (USD, EUR, GBP buying, selling, and mean spreads).

---

## 📸 Interactive Streamlit Dashboard Preview

![Hali Pipeline Dashboard Preview](assets/dashboard_preview.png)

*Live Streamlit dashboard showcasing real-time data freshness, the Pipeline Health audit sidebar, interactive temperature trends, rainfall distribution, and currency dynamics.*

---

## 🏛️ Pipeline Architecture

```mermaid
graph TD
    subgraph Layer 1: EXTRACT [Layer 1: Robust Extraction]
        W_SRC["weather_source.py<br/>(Kenya Met Dept + Fixture Fallback)"]
        N_SRC["nse_source.py<br/>(NSE Daily Prices + Fixture Fallback)"]
        C_SRC["cbk_source.py<br/>(CBK Forex Rates + Fixture Fallback)"]
    end

    subgraph Layer 2: TRANSFORM [Layer 2: Pure-Function Transformation]
        W_TRF["weather_transform.py<br/>(UTC coerce, IQR outlier detection, dedupe)"]
        N_TRF["nse_transform.py<br/>(Dash handling, daily_change_pct, sort)"]
        C_TRF["cbk_transform.py<br/>(Float coercion, dedupe natural key)"]
    end

    subgraph Layer 3: LOAD & VALIDATE [Layer 3: Idempotent Load & Quality Gates]
        LOADER["loader.py<br/>(SQLAlchemy Core ON CONFLICT DO UPDATE)"]
        DQ["quality/checks.py<br/>(Row count, freshness &lt; 26h, duplicates, nulls)"]
    end

    subgraph Storage: PostgreSQL 16 / SQLite [Storage Tier]
        DB_W[(weather_observations)]
        DB_N[(nse_prices)]
        DB_C[(cbk_rates)]
        DB_R[(pipeline_runs)]
        DB_Q[(dq_results)]
    end

    subgraph Orchestration & Delivery [Orchestration & Serving]
        SCHED["scheduler/jobs.py<br/>(APScheduler Cron + Tenacity Retry)"]
        ALERT["Webhook Alerts<br/>(Slack/Telegram on Failure)"]
        DASH["dashboard/app.py<br/>(Streamlit + Plotly Visualizations)"]
    end

    W_SRC --> W_TRF --> LOADER
    N_SRC --> N_TRF --> LOADER
    C_SRC --> C_TRF --> LOADER

    LOADER --> DB_W & DB_N & DB_C
    LOADER --> DQ --> DB_Q
    SCHED --> LOADER
    SCHED --> DB_R
    SCHED -. Failure Alert .-> ALERT

    DB_W & DB_N & DB_C & DB_R --> DASH
```

### Key Engineering Highlights:
- **Resilient Ingestion:** 3-attempt exponential backoff retries via `tenacity`, custom `User-Agent` headers, timeouts, and automatic offline fixture fallbacks.
- **Pure Transformations:** Deterministic, side-effect-free pandas transforms (`DataFrame` in $\to$ `DataFrame` out) with 1.5x IQR outlier detection.
- **Idempotent Loading:** SQLAlchemy Core upsert with `ON CONFLICT DO UPDATE` guarantees rerun safety across PostgreSQL 16 and SQLite.
- **Strict Data Quality Gates:** Post-load assertions enforce row counts, temporal freshness ($< 26$ hours), non-null critical columns, and composite natural key uniqueness.
- **Production Observability:** Structured JSON logging with `structlog`, historical run ledgers (`pipeline_runs`), execution durations, and automated Slack/Telegram webhook alerts on failure.

---

## 📂 Project Structure

```text
Hali-Pipeline/
├── assets/
│   └── dashboard_preview.png              # UI screenshot
├── cli.py                                 # Modular CLI entrypoint
├── config.py                              # Pydantic BaseSettings environment config
├── dashboard/
│   └── app.py                             # Streamlit 3-tab interactive dashboard
├── db/
│   ├── models.py                          # SQLAlchemy Core tables & schemas
│   └── session.py                         # Engine singleton & migration helpers
├── etl/
│   ├── extract/
│   │   ├── weather_source.py              # Kenya Met extractor
│   │   ├── nse_source.py                  # NSE stock prices extractor
│   │   └── cbk_source.py                  # CBK forex rates extractor
│   ├── transform/
│   │   ├── weather_transform.py           # Weather cleaning & IQR outlier detection
│   │   ├── nse_transform.py               # NSE equity cleaning & pct change
│   │   └── cbk_transform.py               # Forex cleaning & schema validation
│   ├── load/
│   │   └── loader.py                      # Core idempotent upsert loader
│   └── quality/
│       └── checks.py                      # Data quality rules & test ledger
├── hali/
│   ├── __init__.py
│   └── __main__.py                        # python -m hali module execution
├── scheduler/
│   └── jobs.py                            # APScheduler cron daemon & webhook dispatcher
├── tests/
│   ├── conftest.py                        # In-memory SQLite testing harness
│   ├── fixtures/                          # Sample CSV fixtures for offline testing
│   │   ├── weather_sample.csv
│   │   ├── nse_sample.csv
│   │   └── cbk_sample.csv
│   ├── test_extract.py                    # Extraction & retry/fallback unit tests
│   ├── test_transform.py                  # Transformation & pure function unit tests
│   ├── test_load.py                       # Idempotent upsert & conflict resolution tests
│   ├── test_quality.py                    # Data quality rule assertions
│   └── test_scheduler_and_cli.py          # Orchestration, CLI, & dashboard helper tests
├── .github/
│   └── workflows/ci.yml                   # GitHub Actions automated CI workflow
├── docker-compose.yml                     # Multi-service topology (Postgres, Scheduler, Dashboard)
├── Dockerfile                             # Container definition for pipeline services
├── Makefile                               # Developer automation targets
├── pyproject.toml                         # Project metadata, Ruff, Mypy & Pytest config
├── requirements.txt                       # Pinned production and test dependencies
├── .env.example                           # Sample environment configuration template
├── README.md                              # Project documentation
└── LICENSE                                # MIT License
```

---

## 📊 Data Dictionary

### 1. `weather_observations`
Telemetric weather readings from Kenya Meteorological Department monitoring stations.

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key (autoincrement) | Internal sequence identifier |
| `station` | `VARCHAR` | No | Composite Unique Key | Weather station identifier (e.g. `NairobiHQ`) |
| `observed_at` | `TIMESTAMPTZ` | No | Composite Unique Key | UTC observation timestamp |
| `temp_c` | `FLOAT` | Yes | - | Temperature in degrees Celsius |
| `rainfall_mm` | `FLOAT` | Yes | - | Precipitation in millimeters |
| `humidity_pct` | `FLOAT` | Yes | - | Relative humidity percentage (0–100%) |
| `is_outlier` | `BOOLEAN` | No | Default `False` | True if flagged as statistical outlier via 1.5x IQR |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | UTC ingestion timestamp |

### 2. `nse_prices`
Daily equity market trading prices and transaction volumes from the Nairobi Securities Exchange.

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key (autoincrement) | Internal sequence identifier |
| `ticker` | `VARCHAR` | No | Composite Unique Key | Stock ticker symbol (e.g. `SCOM`, `EQTY`) |
| `trading_date` | `TIMESTAMPTZ` | No | Composite Unique Key | Date of trading session |
| `open` | `FLOAT` | Yes | - | Opening price in KES |
| `high` | `FLOAT` | Yes | - | Session high in KES |
| `low` | `FLOAT` | Yes | - | Session low in KES |
| `close` | `FLOAT` | Yes | - | Closing price in KES |
| `volume` | `FLOAT` | Yes | - | Total shares traded |
| `daily_change_pct` | `FLOAT` | Yes | - | Percentage change from session baseline |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | UTC ingestion timestamp |

### 3. `cbk_rates`
Official indicative foreign exchange rates against the Kenyan Shilling published by the Central Bank of Kenya.

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key (autoincrement) | Internal sequence identifier |
| `currency` | `VARCHAR` | No | Composite Unique Key | 3-letter currency code (e.g. `USD`, `EUR`, `GBP`) |
| `rate_date` | `TIMESTAMPTZ` | No | Composite Unique Key | Published date of rates |
| `buying` | `FLOAT` | Yes | - | Commercial bank buying rate |
| `selling` | `FLOAT` | Yes | - | Commercial bank selling rate |
| `mean` | `FLOAT` | Yes | - | Central Bank official mean rate |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | UTC ingestion timestamp |

### 4. `pipeline_runs`
Audit and telemetry ledger tracking pipeline executions, durations, and health.

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key (autoincrement) | Run identifier |
| `pipeline_name` | `VARCHAR` | No | - | Pipeline target (`weather`, `nse`, `cbk`) |
| `started_at` | `TIMESTAMPTZ` | No | - | UTC execution start timestamp |
| `finished_at` | `TIMESTAMPTZ` | Yes | - | UTC execution completion timestamp |
| `status` | `VARCHAR` | No | - | Outcome (`running`, `success`, `failed`, `failed_quality`) |
| `rows_loaded` | `INTEGER` | No | Default `0` | Records successfully loaded |
| `error` | `TEXT` | Yes | - | Error stack trace on failure |

### 5. `dq_results`
Data quality check assertion ledger.

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key (autoincrement) | Test identifier |
| `run_id` | `INTEGER` | No | - | Reference to `pipeline_runs.id` |
| `check_name` | `VARCHAR` | No | - | Rule executed (e.g. `weather_observations_freshness`) |
| `passed` | `BOOLEAN` | No | - | Pass/fail status |
| `details` | `TEXT` | Yes | - | Detailed diagnostic logs on failure |
| `run_at` | `TIMESTAMPTZ` | No | Default `NOW()` | UTC check timestamp |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+**
- *(Optional)* **Docker & Docker Compose** (for multi-container deployment)

### 2. Local Installation
```bash
# Clone the repository
git clone https://github.com/yourorg/hali-pipeline.git
cd hali-pipeline

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration (`.env`)
Copy the environment template:
```bash
cp .env.example .env
```

The pipeline supports two modes:
- **Local Standalone Mode (Zero external dependencies):**
  ```ini
  DATABASE_URL=sqlite:///hali.db
  ```
- **PostgreSQL Production Mode:**
  ```ini
  DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hali
  ```

### 4. Running the Pipeline
```bash
# Ingest all data once (runs Weather, NSE, and CBK pipelines)
python -m hali run --pipeline all

# Run individual pipelines
python -m hali run --pipeline weather
python -m hali run --pipeline nse
python -m hali run --pipeline cbk
```

### 5. Launching the Streamlit Dashboard
```bash
python -m hali dashboard
```
Open **http://localhost:8501** in your browser.

---

## 🐳 Docker Deployment

Run the complete production stack (PostgreSQL 16, Background Scheduler, and Streamlit Dashboard) with Docker Compose:

```bash
docker compose up --build -d
```

- **Dashboard:** http://localhost:8501
- **PostgreSQL 16:** `localhost:5432` (`hali` database)
- **Scheduler Service:** Automated cron jobs in `Africa/Nairobi` timezone:
  - 🌦️ **Weather**: Every 6 hours (`0 */6 * * *`)
  - 📈 **NSE Equities**: Weekdays at 18:00 EAT (`0 18 * * 1-5`)
  - 💱 **CBK Forex**: Daily at 09:00 EAT (`0 9 * * *`)

---

## 🧪 Testing & Code Quality

The test suite requires no live network or external databases; it runs against an in-memory SQLite engine with isolated mocks and fixture fallbacks:

```bash
# Run pytest with code coverage (enforces ≥ 80% coverage)
make test
# Or directly:
pytest --cov=etl --cov=db --cov=scheduler --cov=config --cov=cli tests/

# Run static analysis & type checking
make lint
# Or directly:
ruff check .
mypy .
```

---

## ⚖️ Legal & Attribution Notices

- **Nairobi Securities Exchange (NSE)**: Equity trading data is copyrighted by the Nairobi Securities Exchange. When redistributing derived visualisations or reports, maintain appropriate attribution stating: *"Data sourced from Nairobi Securities Exchange (NSE) daily equities bulletin."*
- **Central Bank of Kenya (CBK)**: Foreign exchange rates represent official indicative published rates from the Central Bank of Kenya. These reference rates are provided for informational and analytical purposes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
