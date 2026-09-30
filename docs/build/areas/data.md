# Data Engineering

**Evaluation criterion:** data extraction and transformation. **Owner:** Natalia.

**Requirements:** those in the `data` area in the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../understand/dataset.md) (tables and columns), [system](../../architecture/system-architecture.md), [`sentinel-data-engine/`](../../../sentinel-data-engine/README.md).

## Implementation: `sentinel-data-engine`

The pipeline is fully implemented in the [`sentinel-data-engine/`](../../../sentinel-data-engine/) module as a production-grade **Medallion Architecture** over **Delta Lake**. The same Python package (`sentinel_data`) runs in two modes selected at runtime:

| Mode | Engine | Cost | Trigger |
|---|---|---|---|
| Local development | DuckDB + Delta extension (`INSTALL delta; LOAD delta;`) | $0 — no server, no cloud | `python -m sentinel_data --layer bronze\|silver\|gold` |
| Production (Azure) | Azure Databricks + PySpark + Delta Lake on ADLS Gen2 | Single-node `Standard_DS3_v2` spot | `databricks bundle run medallion_pipeline_job` |

**Source:** AWS S3 Read-Only Bucket (`S3_BUCKET_NAME` in `.env`) — 13 synthetic relational tables, ~19 M records across MX, CO, AR.

## Centralized Data Catalog (`catalog.py`)

[`src/sentinel_data/catalog.py`](../../../sentinel-data-engine/src/sentinel_data/catalog.py) is the **single source of truth** for all 13 LATAM Bank tables. It defines `TableDefinition`, `PartitionStrategy` (DAILY, MONTHLY_SNAPSHOT, FULL_SNAPSHOT), and `QualityRule`. Neither the Bronze ingestor nor the Silver transformer hard-codes any table-specific logic — they consume the catalog at runtime. Composite primary keys (e.g. `daily_exchange_rates`: `date` + `source_currency` + `target_currency`) are handled transparently, with auto-generated MERGE conditions and deduplication partition keys.

## Medallion Architecture

### Bronze Layer — Raw Ingestion (`ingest_bronze.py`)

Append-only and immutable. Every record is enriched with four audit columns: `_source_system`, `_source_file`, `_ingested_at`, `_batch_id`. File-level idempotency is enforced via O(1) set lookup (`_already_ingested_files`) in local mode and Auto Loader checkpointing in Databricks — re-running never produces duplicates.

### Silver Layer — Validation & Curation (`transform_silver.py`)

Schema enforcement and domain validation via `QualityRule` predicates defined in the catalog. Invalid records are split to a non-blocking quarantine table (`silver.rejected_records`) with full raw JSON and semicolon-separated `rejection_reason`. Clean records are deduplicated with `ROW_NUMBER() OVER (PARTITION BY <pk> ORDER BY _ingested_at DESC)` and upserted via idempotent Delta `MERGE INTO`.

### Gold Layer — Denormalized Serving (`build_gold.py`)

Three denormalized tables `sentinel-ai-core/` will read. The folder exists; it does not read Gold yet ([folders](../../../team/plan.md#folders)). Target latency is sub-50ms:

| Table | PK | Key Derived Columns |
|---|---|---|
| `gold_dispute_customer_360` | `customer_id` | `dispute_risk_level`, `active_disputes`, `total_balance`, `avg_csat_score` |
| `gold_dispute_eligible_transactions` | `transaction_id` | `is_disputed`, `days_since_transaction`, `is_eligible_for_dispute` |
| `gold_dispute_cases_summary` | `complaint_id` | `sla_breached`, `case_age_days`, `agent_*`, `origin_sentiment_score` |

`is_eligible_for_dispute` enforces the 90-day dispute window: `NOT is_disputed AND days_since_transaction ≤ 90`. `dispute_risk_level` is deterministically derived (`HIGH` / `MEDIUM` / `LOW`) from `active_disputes` and `is_repeat_complainer`.

## Scope

- **Repeatable, deterministic ETL/ELT pipeline**: same input, same output.
- **Strict schema contracts**: invalid data is quarantined, never enters silently. `catalog.py` is the contract.
- **Quality checks** via `QualityRule` predicates across all 13 tables (~80–130 rules total).
- **Per-customer record isolation**, the basis of access control.
- **Batch incremental** processing: daily fact tables partitioned by `year/month/day`; dimension tables use monthly snapshot or full snapshot. Watermark-based incremental runs via Auto Loader (Databricks) or `_already_ingested_files` set (local).

## Incremental processing

| Mechanism | Local / DuckDB | Databricks |
|---|---|---|
| Idempotency | `_already_ingested_files()` O(1) set lookup | Auto Loader checkpoint directory |
| Deduplication | `ROW_NUMBER()` window on composite PK | Same, in PySpark |
| Upsert | Union + re-deduplicate + COPY OVERWRITE | Delta `MERGE INTO` (`whenMatchedUpdateAll` / `whenNotMatchedInsertAll`) |
| Schema evolution | Catalog-enforced; new columns detected at ingestion | `cloudFiles.schemaLocation` isolated from offsets |

## Evidence for evaluation

- [x] Executable pipeline with a single command (`python -m sentinel_data --layer bronze|silver|gold`)
- [x] Contracts and quality report (`catalog.py` — 13 tables, per-table `QualityRule` lists)
- [x] Idempotent upsert via Delta `MERGE INTO` (cross-batch) and `ROW_NUMBER()` (within-batch)
- [x] Quarantine / rejected records table with source-file traceability
- [x] Test suite: 18 pytest tests covering Bronze idempotency, Silver quarantine, and Gold derivations
- [x] Databricks Asset Bundle (`databricks.yml`) for production deployment
