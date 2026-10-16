# Changelog

All notable changes to Pulse Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-17

### Added
- **Core ETL Architecture**: 3-layer architecture for extract, pure transformation, and idempotent load.
- **Kenya Met Weather Pipeline**: Live extraction with exponential backoff, fixture fallback, and 1.5x IQR outlier detection.
- **NSE Equities Pipeline**: Automated daily stock price ingestion, OHLC normalization, and daily percentage change derivation.
- **CBK Forex Pipeline**: Official daily exchange rate ingestion across USD, EUR, GBP against KES with buy/sell spreads.
- **Data Quality Gates**: Automated validation for table row count, temporal freshness (< 26h SLA), duplicate key detection, and non-null checks.
- **Interactive Streamlit Dashboard**: Dark-mode dashboard featuring live freshness indicator, operational health sidebar, and Plotly interactive time-series charts.
- **Background Scheduler Daemon**: APScheduler integration with cron jobs configured in `Africa/Nairobi` timezone.
- **CLI Subcommands**: `run`, `schedule`, and `dashboard` subcommands via `python -m pulse` and `python -m hali`.
- **Infrastructure & Packaging**:
  - Official GHCR Docker image publishing workflow (`.github/workflows/docker.yml`).
  - GitHub Pages documentation workflow (`.github/workflows/docs.yml`).
  - Automated GitHub Releases workflow (`.github/workflows/release.yml`) with Python wheel and sdist artifact distribution.
  - Multi-container Docker Compose setup for PostgreSQL 16, scheduler daemon, and dashboard.
- **Comprehensive Test Suite**: SQLite in-memory test suite achieving >90% code coverage.
