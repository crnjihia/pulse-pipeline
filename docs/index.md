# 🇰🇪 Pulse Pipeline

> **Automated, production-grade ETL system and real-time observability platform for Kenyan public datasets.**

[![CI Pipeline](https://github.com/crnjihia/pulse-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/crnjihia/pulse-pipeline/actions/workflows/ci.yml)
[![Docker GHCR Package](https://img.shields.io/badge/GHCR-Docker%20Package-blue?logo=docker)](https://github.com/crnjihia/pulse-pipeline/pkgs/container/pulse-pipeline)
[![Documentation](https://img.shields.io/badge/Docs-GitHub%20Pages-brightgreen?logo=github)](https://crnjihia.github.io/pulse-pipeline/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/crnjihia/pulse-pipeline)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is Pulse Pipeline?

Pulse Pipeline is an end-to-end data platform engineered to ingest, clean, validate, store, and serve crucial Kenyan public datasets:

1. **🌦️ Kenya Meteorological Department**: Observational weather telemetry across regional stations (temperature, precipitation, relative humidity, and 1.5x IQR statistical anomaly flags).
2. **📈 Nairobi Securities Exchange (NSE)**: Daily equity trading session data (Open, High, Low, Close prices, trading volume, and calculated daily percentage changes).
3. **💱 Central Bank of Kenya (CBK)**: Official daily indicative foreign exchange rates against the Kenya Shilling (KES) for primary currencies (USD, EUR, GBP) including buy, sell, and mean spreads.

---

## ⚡ Key Highlights

* **Resilient Extraction**: 3-attempt exponential backoff retries with automatic fallback to offline fixtures when upstream portals are unreachable.
* **Pure Functional Transformations**: Deterministic, side-effect-free pandas transforms (`DataFrame` in $\to$ `DataFrame` out) with IQR outlier detection and edge-case sanitization.
* **Dialect-Aware Idempotent Upserts**: SQLAlchemy Core `ON CONFLICT DO UPDATE` ensuring rerun safety on both **PostgreSQL 16** (production) and **SQLite** (local & testing).
* **Automated Data Quality Gates**: Post-load assertions enforcing row count sanity, freshness SLAs ($< 26$ hours), uniqueness on composite natural keys, and null checks.
* **Production Observability**: Full execution audit trail (`pipeline_runs` table), execution duration tracking, structured JSON logging, and Slack/Telegram webhook alerts.
* **Interactive Analytics**: Modern dark-mode Streamlit dashboard with Plotly charts and live data freshness metrics.
* **Containerized & Packaged**: Official GHCR Docker images, Docker Compose stack, and automated semantic releases.

---

## 🚀 Quick Start

### Option A: Pulling the GHCR Docker Image

```bash
docker pull ghcr.io/crnjihia/pulse-pipeline:latest

# Run one-off ingestion
docker run --rm ghcr.io/crnjihia/pulse-pipeline:latest python -m pulse run --pipeline all
```

### Option B: Local Environment

```bash
# Clone repository
git clone https://github.com/crnjihia/pulse-pipeline.git
cd pulse-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all pipelines (defaults to SQLite standalone mode)
python -m pulse run --pipeline all

# Launch interactive analytics dashboard
python -m pulse dashboard
```

---

## 🧭 Documentation Roadmap

* [Architecture & Design](architecture.md): Deep dive into the 3-layer architecture and storage engine.
* [Data Pipelines](pipelines/index.md): Pipeline execution, schedules, and transformations.
* [Data Quality Gates](quality.md): SLA validation, audit ledgers, and alert thresholds.
* [Analytics Dashboard](dashboard.md): Interactive Streamlit and Plotly visualization interface.
* [CLI & Scheduler](cli.md): Command-line reference and APScheduler cron daemon.
* [Deployment & GHCR](deployment.md): Running multi-container Docker Compose or pulling GHCR packages.
* [Releases & Changelog](releases.md): Semantic release versioning strategy and history.
