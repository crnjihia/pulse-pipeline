# Kenya Met Weather Pipeline

The **Kenya Met Weather Pipeline** ingests observational meteorological readings from weather monitoring stations across Kenya.

## Ingestion Details

* **Identifier**: `weather`
* **Cron Schedule**: Every 6 hours (`0 */6 * * *`) in `Africa/Nairobi` timezone
* **Extractor**: `etl/extract/weather_source.py`
* **Transformer**: `etl/transform/weather_transform.py`
* **Destination Table**: `weather_observations`
* **Composite Natural Key**: `(station, observed_at)`

---

## 1.5x IQR Statistical Outlier Detection

To ensure sensor malfunctions or recording glitches do not distort analytics, the transformation layer applies the **Interquartile Range (IQR)** rule on numeric columns (`temp_c`, `rainfall_mm`, `humidity_pct`):

$$\text{IQR} = Q_3 - Q_1$$
$$\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}$$
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$

Observations falling outside $[\text{Lower Bound}, \text{Upper Bound}]$ are flagged with `is_outlier = True` without deleting the raw observation, allowing analysts to filter or audit anomalous events.

---

## Data Schema: `weather_observations`

| Column | Type | Nullable | Constraint | Description |
|:---|:---|:---|:---|:---|
| `id` | `INTEGER` | No | Primary Key | Sequence identifier |
| `station` | `VARCHAR` | No | Natural Key | Station name (e.g., `NairobiHQ`, `MombasaAirport`) |
| `observed_at` | `TIMESTAMPTZ` | No | Natural Key | UTC timestamp of reading |
| `temp_c` | `FLOAT` | Yes | - | Temperature in Celsius |
| `rainfall_mm` | `FLOAT` | Yes | - | Rainfall in millimeters |
| `humidity_pct` | `FLOAT` | Yes | - | Relative humidity percentage |
| `is_outlier` | `BOOLEAN` | No | Default `False` | True if flagged as statistical outlier |
| `ingested_at` | `TIMESTAMPTZ` | No | Default `NOW()` | Timestamp when loaded into DB |
