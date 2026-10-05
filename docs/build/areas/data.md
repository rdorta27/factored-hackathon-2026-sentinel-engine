---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Data Engineering

**Evaluation criterion:** data extraction and transformation.

**Owner:** Natalia.

**Requirements:** the requirements in the `data` area of the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../data/dataset.md) (tables and columns), [system](../../architecture/system-architecture.md) and [`sentinel-data-engine/`](../../../sentinel-data-engine/README.md).

## Implementation: `sentinel-data-engine`

The module [`sentinel-data-engine/`](../../../sentinel-data-engine/) implements the whole pipeline. It is a **Medallion Architecture** over **Delta Lake**. The same Python package (`sentinel_data`) runs in two modes. The runtime selects the mode:

| Mode | Engine | Cost | Trigger |
|---|---|---|---|
| Local development | DuckDB and the Delta extension (`INSTALL delta; LOAD delta;`) | USD 0. No server and no cloud | `python -m sentinel_data --layer bronze\|silver\|gold` |
| Production (Azure) | Azure Databricks, PySpark and Delta Lake on ADLS Gen2 | One node, `Standard_DS3_v2` spot | `databricks bundle run medallion_pipeline_job` |

**Source:** an AWS S3 read-only bucket (`S3_BUCKET_NAME` in `.env`). It holds 13 synthetic relational tables with about 19 M records for MX, CO and AR.

## Centralized Data Catalog (`catalog.py`)

[`src/sentinel_data/catalog.py`](../../../sentinel-data-engine/src/sentinel_data/catalog.py) is the **single source of truth** for the 13 LATAM Bank tables. It defines `TableDefinition`, `PartitionStrategy` (DAILY, MONTHLY_SNAPSHOT, FULL_SNAPSHOT) and `QualityRule`.

- The Bronze ingestor and the Silver transformer have no table-specific logic. They read the catalog at runtime.
- Composite primary keys work without extra code. Example: `daily_exchange_rates` uses `date`, `source_currency` and `target_currency`.
- The code generates the MERGE conditions and the deduplication partition keys.

## Medallion Architecture

### Bronze Layer — Raw Ingestion (`ingest_bronze.py`)

The layer is append-only and immutable. Each record gets four audit columns: `_source_system`, `_source_file`, `_ingested_at` and `_batch_id`. File-level idempotency uses an O(1) set lookup (`_already_ingested_files`) in local mode. It uses Auto Loader checkpointing in Databricks. A second run never creates duplicates.

### Silver Layer — Validation & Curation (`transform_silver.py`)

`QualityRule` predicates in the catalog enforce the schema and validate the domain.

- A non-blocking quarantine table (`silver.rejected_records`) receives each invalid record. It keeps the full raw JSON and a `rejection_reason` that uses semicolons as separators.
- The layer deduplicates clean records with `ROW_NUMBER() OVER (PARTITION BY <pk> ORDER BY _ingested_at DESC)`.
- It upserts them with an idempotent Delta `MERGE INTO`.

### Gold Layer — Denormalized Serving (`build_gold.py`)

The layer builds three denormalized tables for `sentinel-ai-core/`. The service reads the PII-free Gold view when the DuckDB file is present. Otherwise it uses the labeled mock (see the [README](../../../README.md)). The target latency is under 50 ms:

| Table | PK | Key derived columns |
|---|---|---|
| `gold_dispute_customer_360` | `customer_id` | `dispute_risk_level`, `active_disputes`, `total_balance`, `avg_csat_score` |
| `gold_dispute_eligible_transactions` | `transaction_id` | `is_disputed`, `days_since_transaction`, `is_eligible_for_dispute` |
| `gold_dispute_cases_summary` | `complaint_id` | `sla_breached`, `case_age_days`, `agent_*`, `origin_sentiment_score` |

`is_eligible_for_dispute` enforces the 90-day dispute window: `NOT is_disputed AND days_since_transaction ≤ 90`. The code derives `dispute_risk_level` (`HIGH`, `MEDIUM` or `LOW`) from `active_disputes` and `is_repeat_complainer`. The derivation is deterministic.

## Scope

- **Repeatable, deterministic ETL/ELT pipeline:** the same input gives the same output.
- **Strict schema contracts:** the pipeline quarantines invalid data. Invalid data never enters silently. `catalog.py` is the contract.
- **Quality checks:** `QualityRule` predicates cover the 13 tables (about 80 to 130 rules).
- **Per-customer record isolation:** it is the basis of access control.
- **Batch incremental processing:** daily fact tables use partitions by `year/month/day`. Dimension tables use a monthly snapshot or a full snapshot. Incremental runs use a watermark: Auto Loader (Databricks) or the `_already_ingested_files` set (local).

## Incremental processing

| Mechanism | Local / DuckDB | Databricks |
|---|---|---|
| Idempotency | `_already_ingested_files()` O(1) set lookup | Auto Loader checkpoint directory |
| Deduplication | `ROW_NUMBER()` window on composite PK | Same, in PySpark |
| Upsert | Union, re-deduplicate and COPY OVERWRITE | Delta `MERGE INTO` (`whenMatchedUpdateAll` and `whenNotMatchedInsertAll`) |
| Schema evolution | The catalog enforces it. Ingestion detects new columns | `cloudFiles.schemaLocation` is separate from the offsets |

## Evidence for evaluation

- [x] Executable pipeline with one command (`python -m sentinel_data --layer bronze|silver|gold`)
- [x] Contracts and quality report (`catalog.py`: 13 tables, one `QualityRule` list for each table)
- [x] Idempotent upsert with Delta `MERGE INTO` (across batches) and `ROW_NUMBER()` (inside a batch)
- [x] Quarantine table of rejected records, with the source file of each record
- [x] Test suite: 18 pytest tests for Bronze idempotency, Silver quarantine and Gold derivations
- [x] Databricks Asset Bundle (`databricks.yml`) for the production deployment
