# Deployment & GHCR Package

Pulse Pipeline is containerized and published to GitHub Container Registry (GHCR).

---

## 1. Using the Official GHCR Docker Image

Official container images are published automatically on every release and main branch commit:

```bash
# Pull the latest stable image
docker pull ghcr.io/crnjihia/pulse-pipeline:latest

# Or pull a specific release tag
docker pull ghcr.io/crnjihia/pulse-pipeline:0.1.0
```

### Ingestion via Container
```bash
docker run --rm \
  -e DATABASE_URL="postgresql+psycopg2://postgres:postgres@db:5432/pulse" \
  ghcr.io/crnjihia/pulse-pipeline:latest \
  python -m pulse run --pipeline all
```

### Running the Dashboard via Container
```bash
docker run -d --name pulse-dashboard \
  -p 8501:8501 \
  -e DATABASE_URL="postgresql+psycopg2://postgres:postgres@db:5432/pulse" \
  ghcr.io/crnjihia/pulse-pipeline:latest \
  streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
```

---

## 2. Multi-Container Orchestration (Docker Compose)

For complete local or production deployments, use the provided `docker-compose.yml`:

```bash
docker compose up --build -d
```

This starts:
1. `postgres`: PostgreSQL 16 database with health check on port 5432.
2. `scheduler`: Background APScheduler container executing cron runs.
3. `dashboard`: Interactive Streamlit frontend served on port 8501.

To stop the services:
```bash
docker compose down
```

---

## 3. Environment Variables Reference

| Variable | Default Value | Description |
|:---|:---|:---|
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/pulse` | Connection string for target database (Postgres or SQLite) |
| `WEBHOOK_URL` | `None` | Optional Slack or Telegram webhook URL for error alerts |
| `USER_AGENT` | `PulsePipeline/1.0 (...)` | HTTP User-Agent header used during extraction |
