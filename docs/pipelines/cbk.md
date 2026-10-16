# Central Bank of Kenya (CBK) Forex Pipeline

The **CBK Forex Pipeline** ingests official indicative foreign exchange rates published by the Central Bank of Kenya.

## Ingestion Details

* **Identifier**: `cbk`
* **Cron Schedule**: Daily at 09:00 EAT (`0 9 * * *`)
* **Extractor**: `etl/extract/cbk_source.py`
* **Transformer**: `etl/transform/cbk_transform.py`
* **Destination Table**: `cbk_rates`
* **Composite Natural Key**: `(currency, rate_date)`

---

## Transformation Logic & Spreads

* **Column Standardisation**: Accepts either `date` or `rate_date` from raw feeds and standardises to UTC datetime.
* **Rate Parsing**: Coerces buying, selling, and mean exchange rates into floating point values.
* **Natural Key Enforcement**: Drops duplicate `(currency, rate_date)` records and sorts chronologically.

---

## Data Schema: `cbk_rates`

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key | Sequence identifier |
| `currency` | `VARCHAR` | No | Natural Key | Currency symbol (e.g. `USD`, `EUR`, `GBP`) |
| `rate_date` | `TIMESTAMPTZ` | No | Natural Key | Published date of official rates |
| `buying` | `FLOAT` | Yes | - | Commercial bank buying rate in KES |
| `selling` | `FLOAT` | Yes | - | Commercial bank selling rate in KES |
| `mean` | `FLOAT` | Yes | - | Official Central Bank mean rate in KES |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Timestamp when loaded into DB |
