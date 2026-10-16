# Data Quality Gates & Ingestion Audit

Pulse Pipeline enforces strict **Data Quality (DQ) Gates** executed after every ingestion cycle. If critical checks fail, the pipeline run is flagged as `failed_quality`, failure details are recorded in the database, and webhook alerts are triggered.

---

## The Four Quality Rules

The quality module is implemented in `etl/quality/checks.py`:

### 1. Row Count Check
Verifies that the target table contains records after the load step.
```python
def check_row_count(engine: Engine, table: Table, run_id: int) -> bool:
    stmt = select(func.count()).select_from(table)
    with engine.begin() as conn:
        count = conn.scalar(stmt) or 0
    return count > 0
```

### 2. Temporal Freshness Check
Ensures that data is not stale. The latest observation timestamp must be within an age window (default: **26 hours**).
```python
age = datetime.now(UTC) - max_date
passed = age <= timedelta(hours=max_age_hours)
```

### 3. Duplicate Prevention Check
Executes a SQL aggregation assertion on composite natural keys:
```sql
SELECT {natural_key}, COUNT(*) 
FROM {table} 
GROUP BY {natural_key} 
HAVING COUNT(*) > 1;
```
If any duplicate key is returned, the check immediately fails.

### 4. Non-Null Critical Columns
Validates that essential business fields (e.g., `close` price for equities, `station` for weather, `buying` rate for forex) do not contain nulls.

---

## Audit Ledgers

Every check execution is permanently audited in the `dq_results` table:

```sql
SELECT check_name, passed, details, run_at 
FROM dq_results 
ORDER BY run_at DESC 
LIMIT 10;
```

| Column | Description |
|:---|:---|
| `run_id` | Foreign identifier linking to `pipeline_runs.id` |
| `check_name` | Name of the evaluated assertion (e.g. `nse_prices_freshness`) |
| `passed` | Boolean pass/fail indicator |
| `details` | Diagnostic explanation if the rule failed |
| `run_at` | UTC timestamp of assertion |
