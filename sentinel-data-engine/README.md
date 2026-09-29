# Sentinel Data Engine

> **Factored AI & Data Hackathon 2026** — Team Sentinel  
> Production-grade Medallion data pipeline over the LATAM Bank Synthetic Dataset  
> (~19 M records · 13 relational tables · Mexico, Colombia & Argentina)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Architecture](#3-architecture)
   - 3.1 [Medallion Pattern](#31-medallion-pattern)
   - 3.2 [Dual Execution Engine](#32-dual-execution-engine)
4. [Centralized Data Catalog](#4-centralized-data-catalog)
5. [Bronze Layer — Raw Ingestion](#5-bronze-layer--raw-ingestion)
   - 5.1 [Audit Metadata](#51-audit-metadata)
   - 5.2 [File-Level Idempotency](#52-file-level-idempotency)
   - 5.3 [Partition-Aware S3 Paths](#53-partition-aware-s3-paths)
6. [Silver Layer — Validation & Curation](#6-silver-layer--validation--curation)
   - 6.1 [Data Quality Rules](#61-data-quality-rules)
   - 6.2 [Quarantine Pattern](#62-quarantine-pattern)
   - 6.3 [Deduplication & Delta MERGE](#63-deduplication--delta-merge)
7. [Dataset — 13 Source Tables](#7-dataset--13-source-tables)
8. [Deployment — Databricks Asset Bundle](#8-deployment--databricks-asset-bundle)
9. [Local Development Quickstart](#9-local-development-quickstart)
10. [Testing](#10-testing)
11. [Configuration Reference](#11-configuration-reference)
12. [Contributing](#12-contributing)

---

## 1. Project Overview

**Sentinel Data Engine** is the data backbone of the Sentinel Engine project for Factored Datathon 2026. It implements a production-grade **Medallion Architecture** on top of **Delta Lake** to ingest, validate, deduplicate, and serve the LATAM Bank synthetic dataset.

The pipeline is designed around two guiding principles:

| Principle | Implementation |
|---|---|
| **Zero cloud cost during development** | DuckDB with the Delta extension processes local CSV samples without any Spark or cloud infrastructure |
| **Enterprise-grade cloud deployment** | Azure Databricks, PySpark Auto Loader, Unity Catalog, and Databricks Asset Bundles handle production scale |

The same Python package (`sentinel_data`) runs in both environments — the execution engine is selected at runtime via `--run-mode local|databricks`.

---

## 2. Repository Structure

```
sentinel-data-engine/
├── pyproject.toml                          # Package build config — produces sentinel_data.whl
├── databricks.yml                          # Databricks Asset Bundle: artifact + pipeline job
├── .env.example                            # Environment variable template (copy → .env)
├── .gitignore
│
├── src/sentinel_data/
│   ├── __init__.py
│   ├── __main__.py                         # Unified CLI entry point (--layer bronze|silver|gold)
│   ├── catalog.py                          # ★ Central source of truth for all 13 tables
│   │
│   ├── bronze/
│   │   ├── __init__.py
│   │   └── ingest_bronze.py               # BronzeIngestor — append-only raw ingestion
│   │
│   ├── silver/
│   │   ├── __init__.py
│   │   └── transform_silver.py            # SilverTransformer — validate, quarantine, merge
│   │
│   └── gold/
│       ├── __init__.py
│       └── build_gold.py                  # GoldBuilder — denormalized dispute serving tables
│
├── tests/
│   ├── test_ingest_bronze.py              # Bronze idempotency + metadata tests (6 tests)
│   ├── test_silver_quarantine.py          # Silver quarantine split tests (6 tests)
│   └── test_gold_builder.py               # Gold derivation + eligibility tests (13 tests)
│
└── data/                                  # Local sample data (git-ignored)
    ├── raw/<table>/year=*/month=*/day=*/  # Source CSVs (mirrors S3 partition layout)
    ├── bronze/<table>/                    # Bronze Delta tables
    └── silver/<table>/                    # Silver Delta tables
```

---

## 3. Architecture

### 3.1 Medallion Pattern

```
S3 / local CSV
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  BRONZE  (append-only, immutable)                       │
│  • Raw records as received from source                  │
│  • +_source_system  +_source_file                       │
│  • +_ingested_at    +_batch_id                          │
│  • File-level idempotency (skip already-seen files)     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  SILVER  (curated, deduplicated)                        │
│  • Quality validation → quarantine split                │
│  • Window deduplication on primary key(s)               │
│  • Delta MERGE INTO on full PK condition                │
│  • rejected_records table for non-blocking quarantine   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  GOLD  (denormalized, dispute-ready, sub-50ms serving)  │
│  • gold_dispute_customer_360 (1 row/customer)           │
│  • gold_dispute_eligible_transactions (1 row/txn)       │
│  • gold_dispute_cases_summary (1 row/complaint)         │
│  • Pre-computed flags: is_eligible_for_dispute,         │
│    dispute_risk_level, sla_breached                     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Dual Execution Engine

| Dimension | Local Mode | Databricks Mode |
|---|---|---|
| **Engine** | DuckDB + Delta extension | PySpark + delta-spark |
| **Source** | `./data/raw/<table>/` | `s3://factored-datathon-2026-s3-157725502942-us-east-2-an/` |
| **Sink** | `./data/bronze/` or `./data/silver/` | Unity Catalog managed Delta tables |
| **Idempotency** | `_already_ingested_files()` set lookup | Auto Loader checkpoint directory |
| **Cost** | Zero (runs on a laptop) | Single-node `Standard_DS3_v2` spot cluster |
| **Trigger** | `python -m sentinel_data …` | `databricks bundle run medallion_pipeline_job` |

---

## 4. Centralized Data Catalog

**File:** [`src/sentinel_data/catalog.py`](src/sentinel_data/catalog.py)

`catalog.py` is the **single source of truth** for every schema, primary key, partition strategy, and quality contract across all 13 source tables. Neither the Bronze ingestor nor the Silver transformer hard-codes any table-specific logic — they consume the catalog at runtime.

### Core types

```python
class PartitionStrategy(str, Enum):
    DAILY            = "daily"             # year/month/day  (fact tables)
    MONTHLY_SNAPSHOT = "monthly_snapshot"  # year/month      (slowly-changing dims)
    FULL_SNAPSHOT    = "full_snapshot"     # flat prefix      (reference/static dims)

class QualityRule(BaseModel):
    rule_name:     str   # unique identifier — appears in rejection_reason
    column:        str   # column the predicate targets
    sql_predicate: str   # SQL expression returning TRUE for a VALID row

class TableDefinition(BaseModel):
    table_name:         str
    primary_keys:       list[str]          # single or composite
    partition_column:   str
    partition_strategy: PartitionStrategy
    approximate_rows:   int
    quality_rules:      list[QualityRule]

    # Computed properties consumed by SilverTransformer
    @property
    def merge_condition(self) -> str: ...      # "target.k1 = source.k1 AND ..."
    @property
    def dedup_partition_keys(self) -> str: ... # "k1, k2, ..."
```

### Auto-generated MERGE conditions

Composite primary keys are handled transparently. For example, `daily_exchange_rates` has a three-column PK and the catalog produces:

```sql
-- merge_condition (used in Delta MERGE INTO)
target.date = source.date
AND target.source_currency = source.source_currency
AND target.target_currency = source.target_currency

-- dedup_partition_keys (used in ROW_NUMBER OVER PARTITION BY)
date, source_currency, target_currency
```

### Registry summary

| Table | Type | PK(s) | Partition Strategy | Quality Rules | ~Rows |
|---|---|---|---|---|---|
| `customers` | Dimension | `customer_id` | MONTHLY_SNAPSHOT | 15 | 150 K |
| `products` | Dimension | `product_id` | MONTHLY_SNAPSHOT | 12 | 400 K |
| `branches` | Dimension | `branch_id` | FULL_SNAPSHOT | 16 | 350 |
| `service_agents` | Dimension | `agent_id` | MONTHLY_SNAPSHOT | 13 | 1.2 K |
| `marketing_campaigns` | Dimension | `campaign_id` | FULL_SNAPSHOT | 8 | 200 |
| `transactions` | Fact | `transaction_id` | DAILY | 13 | 5 M |
| `call_center_interactions` | Fact | `interaction_id` | DAILY | 13 | 800 K |
| `call_transcripts` | Fact | `transcript_id` | DAILY | 10 | 200 K |
| `satisfaction_surveys` | Fact | `survey_id` | DAILY | 8 | 250 K |
| `digital_events` | Fact | `event_id` | DAILY | 8 | 10 M |
| `complaints` | Fact | `complaint_id` | DAILY | 12 | 80 K |
| `campaign_sends` | Fact | `send_id` | DAILY | 9 | 2 M |
| `daily_exchange_rates` | Reference | `date`, `source_currency`, `target_currency` | DAILY | 5 | 3 K |

---

## 5. Bronze Layer — Raw Ingestion

**File:** [`src/sentinel_data/bronze/ingest_bronze.py`](src/sentinel_data/bronze/ingest_bronze.py)  
**Class:** `BronzeIngestor`

The Bronze layer is **append-only and immutable**. Records are never modified after landing here. The sole transformation applied is the addition of four audit columns that make every row traceable back to its exact source file and ingestion run.

### 5.1 Audit Metadata

Every raw record is enriched with:

| Column | Type | Description |
|---|---|---|
| `_source_system` | `VARCHAR` | Logical name of the originating system (default: `"s3"`) |
| `_source_file` | `VARCHAR` | Absolute path or S3 URI of the originating file |
| `_ingested_at` | `TIMESTAMP` | ISO 8601 UTC timestamp of the ingestion run |
| `_batch_id` | `VARCHAR` | UUID grouping all files processed in the same `BronzeIngestor.run()` call |

These columns are the foundation for Silver deduplication (ordered by `_ingested_at DESC`) and for the quarantine record's `source_file` field.

### 5.2 File-Level Idempotency

Re-running the ingestor over the same directory **never produces duplicate records**.

**Local / DuckDB mode (`_already_ingested_files`)**

```python
def _already_ingested_files(self, con, delta_path) -> set[str]:
    # Queries DISTINCT _source_file from the existing Bronze Delta table.
    # Returns an empty set on first run (table absent) so behaviour is
    # identical across first and subsequent runs.
    rows = con.execute(
        "SELECT DISTINCT _source_file FROM delta_scan('{delta_path}')"
    ).fetchall()
    return {row[0] for row in rows}
```

Before each CSV file is appended, its resolved absolute path is checked against this set in **O(1)**. If present, the file is skipped with a `WARNING` log entry and the Delta table is never touched. Counters `appended` and `skipped` are reported on completion.

**Databricks / Auto Loader mode**

Auto Loader writes a per-table checkpoint at `<checkpoint_base>/<table_name>/`. The checkpoint records the S3 path and commit offset of every file delivered to the Delta table. On re-execution, the stream resumes from the last committed offset, so already-ingested S3 objects are never re-delivered.

`cloudFiles.schemaLocation` is stored in a **sub-path** of the checkpoint directory, isolating schema evolution (adding a source column) from file-tracking history so that schema changes do not reset the processed-file record.

```
<checkpoint_base>/
└── transactions/
    ├── offsets/       ← file-tracking history (idempotency)
    ├── commits/
    └── _schema/       ← inferred schema (isolated from offsets)
```

### 5.3 Partition-Aware S3 Paths

The Bronze ingestor builds the correct S3 source path from the catalog's `PartitionStrategy`:

| Strategy | S3 path constructed |
|---|---|
| `DAILY` (scoped by `partition_date`) | `s3://<bucket>/<table>/year=YYYY/month=MM/day=DD/` |
| `DAILY` (full scan) | `s3://<bucket>/<table>/` |
| `MONTHLY_SNAPSHOT` | `s3://<bucket>/<table>/` |
| `FULL_SNAPSHOT` | `s3://<bucket>/<table>/` |

Setting `partition_date` on the config scopes a Databricks Job task to exactly one daily partition without scanning the full prefix — useful for incremental daily runs.

---

## 6. Silver Layer — Validation & Curation

**File:** [`src/sentinel_data/silver/transform_silver.py`](src/sentinel_data/silver/transform_silver.py)  
**Class:** `SilverTransformer`

The Silver layer enforces the quality contract for each table. Quality rules and primary keys are resolved automatically from `catalog.py` — no table-specific logic exists inside the transformer itself.

### 6.1 Data Quality Rules

Rules are declared as `QualityRule` objects in the catalog and compiled at runtime into a single SQL expression per row:

```sql
-- Example compiled validation expression for transactions
TRIM(BOTH ';' FROM (
    CASE WHEN NOT (transaction_id IS NOT NULL)
         THEN 'transaction_id_not_null' ELSE '' END
    || ';' ||
    CASE WHEN NOT (amount IS NOT NULL)
         THEN 'amount_not_null' ELSE '' END
    || ';' ||
    CASE WHEN NOT (fraud_score IS NULL OR (fraud_score >= 0.0 AND fraud_score <= 1.0))
         THEN 'fraud_score_range' ELSE '' END
    -- ... (13 rules total for transactions)
))
```

The result is an empty string for clean rows, or a semicolon-separated list of failed rule names for invalid rows.

**Rule categories applied across all 13 tables:**

| Category | Example rule | Tables |
|---|---|---|
| **NOT NULL — PK / FK** | `transaction_id IS NOT NULL` | All |
| **NOT NULL — required strings** | `LENGTH(TRIM(city)) > 0` | customers, branches, … |
| **ISO currency length** | `LENGTH(currency) = 3` | transactions, products, … |
| **Score range** | `fraud_score BETWEEN 0.0 AND 1.0` | transactions |
| **Score range** | `main_score BETWEEN 0 AND 10` | satisfaction_surveys |
| **Rate positivity** | `exchange_rate > 0` | daily_exchange_rates |
| **Temporal coherence** | `end_date >= start_date` | marketing_campaigns |
| **Duration non-negative** | `duration_seconds >= 0` | call_transcripts |
| **Confidence range** | `accent_confidence BETWEEN 0.0 AND 1.0` | call_transcripts |
| **Sentiment range** | `sentiment_score BETWEEN -1.0 AND 1.0` | call_center_interactions |

### 6.2 Quarantine Pattern

Failed records are **never dropped and never block pipeline execution**. They are split into a separate quarantine payload and appended to `<catalog>.silver.rejected_records`.

**Quarantine record schema:**

| Column | Description |
|---|---|
| `raw_record` | Full original row serialized as JSON |
| `rejection_reason` | Semicolon-separated list of failed rule names (e.g. `"amount_not_null;currency_not_null"`) |
| `rejected_at` | ISO 8601 UTC timestamp of the rejection |
| `source_file` | Value from the row's `_source_file` audit column |

This schema allows the data quality team to:
- Replay specific files after a source fix (`source_file`).
- Triage failures by rule frequency (`rejection_reason`).
- Reconstruct the exact original payload (`raw_record`).

### 6.3 Deduplication & Delta MERGE

**Within-batch deduplication** uses a window function on the composite primary key:

```sql
ROW_NUMBER() OVER (
    PARTITION BY <pk1>[, <pk2>, ...]
    ORDER BY _ingested_at DESC, _source_file DESC
) AS rn
```

Only rows where `rn = 1` reach the MERGE step. The `_ingested_at DESC` ordering ensures the most recent Bronze record wins when duplicates exist within the same batch.

**Cross-batch idempotency via Delta MERGE:**

```
-- Databricks (PySpark)
DeltaTable.alias("target")
  .merge(deduped_df.alias("source"), merge_condition)
  .whenMatchedUpdateAll()
  .whenNotMatchedInsertAll()
  .execute()

-- Local (DuckDB approximation)
-- Union Silver + incoming → re-deduplicate → COPY OVERWRITE
```

The `merge_condition` is auto-generated by `TableDefinition.merge_condition` and covers all primary key columns, including composite keys:

```sql
-- daily_exchange_rates
target.date = source.date
AND target.source_currency = source.source_currency
AND target.target_currency = source.target_currency
```

Re-running the Silver transformer over the same Bronze data **always produces an identical Silver state** — it is safe to re-trigger without manual cleanup.

---

## 7. Dataset — 13 Source Tables

**S3 Bucket:** `factored-datathon-2026-s3-157725502942-us-east-2-an`  
**Region:** `us-east-2`

### Dimension Tables (slowly-changing, partitioned monthly or full snapshot)

| Table | Rows | Partition | Primary Key |
|---|---|---|---|
| `customers` | 150 K | monthly_snapshot | `customer_id` |
| `products` | 400 K | monthly_snapshot | `product_id` |
| `branches` | 350 | full_snapshot | `branch_id` |
| `service_agents` | 1.2 K | monthly_snapshot | `agent_id` |
| `marketing_campaigns` | 200 | full_snapshot | `campaign_id` |

### Fact Tables (high-volume, partitioned daily by `process_date`)

| Table | Rows | Primary Key |
|---|---|---|
| `transactions` | 5 M | `transaction_id` |
| `call_center_interactions` | 800 K | `interaction_id` |
| `call_transcripts` | 200 K | `transcript_id` |
| `satisfaction_surveys` | 250 K | `survey_id` |
| `digital_events` | 10 M | `event_id` |
| `complaints` | 80 K | `complaint_id` |
| `campaign_sends` | 2 M | `send_id` |

### Reference Table

| Table | Rows | Primary Key |
|---|---|---|
| `daily_exchange_rates` | 3 K | `date`, `source_currency`, `target_currency` |

---

## 8. Deployment — Databricks Asset Bundle

**File:** [`databricks.yml`](databricks.yml)

The bundle defines the complete deployment in a single declarative file:

```
Bundle: sentinel-data-engine
│
├── Artifact: sentinel_wheel (type: whl)
│   └── build: python -m build --wheel --outdir dist/
│
└── Job: medallion_pipeline_job
    ├── Cluster: single-node Standard_DS3_v2 (spot), local[*,4]
    │
    ├── Task: bronze_transactions      ──┐
    ├── Task: bronze_digital_events    ──┤  parallel Bronze tasks
    │                                    │
    ├── Task: silver_transactions  ←─────┘ (depends_on: bronze_transactions)
    └── Task: silver_digital_events   ←─── (depends_on: bronze_digital_events)
```

Each task runs a `python_wheel_task` pointing to `sentinel_data.__main__` with `--layer` and `--table-name` parameters.

```bash
# Deploy to the dev target
databricks bundle deploy --target dev

# Run the full Bronze → Silver pipeline
databricks bundle run medallion_pipeline_job --target dev

# Run a single table task manually
databricks bundle run medallion_pipeline_job --target dev \
  --task bronze_transactions
```

---

## 9. Local Development Quickstart

### Prerequisites

- Python 3.10+
- Internet access for the one-time DuckDB delta extension download

### Setup

```bash
# 1. Clone and enter the repository
git clone https://github.com/your-org/sentinel-data-engine.git
cd sentinel-data-engine

# 2. Create a virtual environment and install all dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 3. Configure environment variables
cp .env.example .env
# Edit .env and fill in AWS credentials and local paths
```

### Run the pipeline locally

```bash
# Ingest a single table into the local Bronze layer
python -m sentinel_data --layer bronze --table-name transactions

# Validate and promote Bronze → Silver
python -m sentinel_data --layer silver --table-name transactions

# Process all 13 tables (Bronze then Silver)
for table in customers products branches service_agents marketing_campaigns \
             transactions call_center_interactions call_transcripts \
             satisfaction_surveys digital_events complaints \
             campaign_sends daily_exchange_rates; do
  python -m sentinel_data --layer bronze --table-name "$table"
  python -m sentinel_data --layer silver --table-name "$table"
done
```

### Build the Python wheel

```bash
pip install build
python -m build --wheel --outdir dist/
# Produces: dist/sentinel_data-0.1.0-py3-none-any.whl
```

### Expected local directory layout after a full run

```
data/
├── raw/
│   └── transactions/
│       └── year=2026/month=01/day=15/
│           └── part-0001.csv
├── bronze/
│   └── transactions/            ← Delta table (immutable append-only)
│       ├── _delta_log/
│       └── part-*.parquet
├── silver/
│   ├── transactions/             ← Delta table (curated, deduplicated)
│   │   ├── _delta_log/
│   │   └── part-*.parquet
│   └── rejected_records/         ← Quarantine Delta table
│       ├── _delta_log/
│       └── part-*.parquet
└── gold/
    ├── gold_dispute_customer_360/       ← 1 row per customer (risk level, balances, CSAT)
    │   ├── _delta_log/
    │   └── part-*.parquet
    ├── gold_dispute_eligible_transactions/  ← 1 row per transaction (eligibility flags)
    │   ├── _delta_log/
    │   └── part-*.parquet
    └── gold_dispute_cases_summary/      ← 1 row per complaint (SLA, agent, sentiment)
        ├── _delta_log/
        └── part-*.parquet
```

---

## 10. Testing

All tests run locally with DuckDB — no Spark session, no S3 credentials required.

```bash
# Run the full test suite
pytest tests/ -v

# Skip tests that require the DuckDB delta extension (e.g. restricted network)
SKIP_DELTA_TESTS=1 pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=sentinel_data --cov-report=term-missing
```

### Test matrix

**`tests/test_ingest_bronze.py`** — 6 tests

| Test | Validates |
|---|---|
| `test_bronze_local_ingestion_creates_delta_table` | Delta table is created; row count matches source |
| `test_bronze_local_ingestion_adds_metadata_columns` | All 4 audit columns present and non-null |
| `test_idempotency_no_duplicates_on_second_run` | Row count unchanged after running twice |
| `test_idempotency_skips_already_ingested_files` | Zero rows appended on second run |
| `test_new_file_added_between_runs_is_ingested` | New file added between runs is picked up; original file not re-processed |
| `test_config_defaults_are_sane` | Config model instantiates correctly with minimal arguments |

**`tests/test_silver_quarantine.py`** — 6 tests

| Test | Validates |
|---|---|
| `test_valid_rows_reach_silver` | All-valid input reaches Silver |
| `test_invalid_rows_routed_to_quarantine` | Null PK row goes to `rejected_records`, not Silver |
| `test_rejection_reason_content` | `rejection_reason` names every failed rule |
| `test_mixed_input_split_correctly` | 2 valid + 1 invalid → correct split counts |
| `test_deduplication_keeps_latest_row` | Duplicate PK → only the latest `_ingested_at` survives |
| `test_quarantine_schema_has_required_columns` | `raw_record`, `rejection_reason`, `rejected_at`, `source_file` all present |

---

## 11. Configuration Reference

### Environment variables (`.env`)

| Variable | Required | Description |
|---|---|---|
| `S3_BUCKET_NAME` | Cloud | Source S3 bucket name |
| `AWS_DEFAULT_REGION` | Cloud | AWS region (`us-east-2`) |
| `AWS_ACCESS_KEY_ID` | Cloud | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Cloud | AWS secret key |
| `LOCAL_RAW_DATA_DIR` | Local | Root directory for raw CSV files |
| `LOCAL_BRONZE_DATA_DIR` | Local | Root directory for Bronze Delta tables |
| `LOCAL_SILVER_DATA_DIR` | Local | Root directory for Silver Delta tables |
| `DATABRICKS_HOST` | Cloud | Workspace URL |
| `DATABRICKS_TOKEN` | Cloud | Personal access token |
| `DATABRICKS_CATALOG` | Cloud | Unity Catalog catalog name (default: `sentinel`) |
| `DATABRICKS_SCHEMA_BRONZE` | Cloud | Bronze schema name (default: `bronze`) |
| `DATABRICKS_SCHEMA_SILVER` | Cloud | Silver schema name (default: `silver`) |

### CLI reference (`python -m sentinel_data`)

```
--layer          bronze | silver | gold   (required)
--table-name     <table>                  (required for bronze/silver; omit for gold)
--run-mode       local | databricks       (default: local)

Bronze-only:
--s3-bucket      <bucket-name>
--s3-prefix      <optional-key-prefix>
--source-system  <label>                  (default: s3)
--partition-date YYYY-MM-DD               (scope daily tables to one partition)
--databricks-schema  <schema>             (default: bronze)

Silver-only:
--databricks-schema-bronze  <schema>      (default: bronze)
--databricks-schema-silver  <schema>      (default: silver)
--databricks-catalog        <catalog>     (default: sentinel)
```

---

## 12. Contributing

1. Branch from `main` using the format `feat/<short-description>` or `fix/<short-description>`.
2. All code must follow the constraints below — the CI linter enforces them:
   - English-only identifiers, comments, docstrings, and log messages.
   - `snake_case` for functions and variables; `PascalCase` for classes.
   - Line length ≤ 100 characters (`ruff` is pre-configured).
   - Full type hints on all public functions and methods.
3. Add or update tests for every changed behaviour. Coverage must not decrease.
4. Open a pull request against `main` and request a review from at least one teammate.

---

> **Factored Datathon 2026** — Sentinel Engine Team  
> Built with DuckDB · Delta Lake · PySpark · Databricks Asset Bundles

---

## 13. Gold Layer: Denormalized Serving Layer for Dispute Intake

The Gold Layer is a high-speed data serving layer engineered specifically for the
real-time AI Dispute Assistant and policy execution engine.

### Architectural Justification: Why Denormalized Gold Tables?

1. **Sub-50ms Query Latency**
   Real-time conversational AI and RAG tool calls require immediate context
   retrieval.  Performing multi-table relational joins
   (`transactions` ⨝ `customers` ⨝ `products` ⨝ `complaints`) at query time
   introduces high database CPU overhead and latency spikes.  Denormalizing
   data into single flat tables indexed by key entities enables O(1)
   point-lookups by `customer_id`, `transaction_id`, or `complaint_id`.

2. **Deterministic Dispute Policy Enforcement**
   Pre-computing business logic flags—such as transaction dispute eligibility
   (`is_eligible_for_dispute`), customer dispute history
   (`is_repeat_complainer`), and SLA status (`sla_breached`)—ensures that the
   AI Agent evaluates claims against verified, deterministic rules rather than
   relying on LLM inference for data joins or flag evaluation.

3. **Decoupled API Consumption**
   Backend endpoints (FastAPI) consume single Gold tables directly, providing
   zero-coupling between raw operational data structures and customer-facing APIs.

### Gold Schema Overview

| Table | PK | Granularity | Key Derived Columns |
|---|---|---|---|
| `gold_dispute_customer_360` | `customer_id` | 1 row per customer | `dispute_risk_level`, `active_disputes`, `total_balance`, `avg_csat_score` |
| `gold_dispute_eligible_transactions` | `transaction_id` | 1 row per transaction | `is_disputed`, `days_since_transaction`, `is_eligible_for_dispute` |
| `gold_dispute_cases_summary` | `complaint_id` | 1 row per complaint | `sla_breached`, `case_age_days`, `agent_*`, `origin_sentiment_score` |

### `gold_dispute_customer_360`

Single-row customer view aggregating demographics, credit score, total product
balances, historical dispute counts, and overall CSAT profile.

| Column | Type | Description |
|---|---|---|
| `customer_id` | VARCHAR | Primary key |
| `total_products` | BIGINT | All products held |
| `active_products` | BIGINT | Products with `product_status = 'ACTIVE'` |
| `total_balance` | DOUBLE | Sum of `current_balance` across all products |
| `total_complaints` | BIGINT | Historical complaint count |
| `active_disputes` | BIGINT | Open complaints (not CLOSED / RESOLVED) |
| `is_repeat_complainer` | BOOLEAN | True if any complaint has the flag set |
| `total_compensation_paid` | DOUBLE | Sum of `compensation_amount` |
| `avg_csat_score` | DOUBLE | Average `main_score` from satisfaction surveys |
| `dispute_risk_level` | VARCHAR | `HIGH` / `MEDIUM` / `LOW` (derived) |
| `snapshot_date` | DATE | `CURRENT_DATE` at build time |

**`dispute_risk_level` derivation:**

```
HIGH   → active_disputes >= 3 OR is_repeat_complainer = TRUE
MEDIUM → active_disputes IN (1, 2)
LOW    → active_disputes = 0 AND is_repeat_complainer = FALSE
```

### `gold_dispute_eligible_transactions`

Denormalized transaction history pre-joined with customer profiles and existing
open complaints, featuring derived eligibility indicators.

| Column | Type | Description |
|---|---|---|
| `transaction_id` | VARCHAR | Primary key |
| `customer_*` | various | Denormalized from `customers` |
| `is_disputed` | BOOLEAN | True when an open complaint references this transaction |
| `days_since_transaction` | BIGINT | `CURRENT_DATE − transaction_date` |
| `is_eligible_for_dispute` | BOOLEAN | `NOT is_disputed AND days_since_transaction ≤ 90` |
| `snapshot_date` | DATE | `CURRENT_DATE` at build time |

### `gold_dispute_cases_summary`

Comprehensive dispute lifecycle tracker joining complaints with assigned service
agents, SLA breach metrics, and origin interaction context.

| Column | Type | Description |
|---|---|---|
| `complaint_id` | VARCHAR | Primary key |
| `sla_breached` | BOOLEAN | Sourced from `complaints.sla_breached` |
| `case_age_days` | BIGINT | `resolution_date − creation_date` (or `CURRENT_DATE` if open) |
| `agent_first_name` / `agent_last_name` | VARCHAR | Assigned agent from `service_agents` |
| `agent_type` / `agent_experience_level` | VARCHAR | Agent classification |
| `origin_sentiment_score` | DOUBLE | Sentiment from the most recent `call_center_interactions` row |
| `origin_channel` | VARCHAR | Channel of most recent interaction |
| `snapshot_date` | DATE | `CURRENT_DATE` at build time |

### Running the Gold Build

**Local (DuckDB):**
```bash
python -m sentinel_data --layer gold
```

**Databricks:**
```bash
databricks bundle run medallion_pipeline_job --target prod
```

**Output directories (local):**
```
data/gold/
├── gold_dispute_customer_360/
├── gold_dispute_eligible_transactions/
└── gold_dispute_cases_summary/
```

### Gold Tests

```bash
python3 -m pytest tests/test_gold_builder.py -v
```

| Test | Validates |
|---|---|
| `test_aggregates_products_and_complaints` | Correct product count, balance, active dispute count, risk level |
| `test_no_products_yields_zero_balance` | Zero totals for customers with no products |
| `test_risk_level_high_for_repeat_complainers` | `HIGH` risk when `is_repeat_complainer` is True |
| `test_avg_csat_score` | CSAT average computed correctly from multiple surveys |
| `test_is_disputed_flag_true` | `is_disputed=True` when open complaint references transaction |
| `test_is_disputed_flag_false_for_undisputed` | `is_disputed=False` when no complaint exists |
| `test_eligible_for_recent_undisputed_transaction` | `is_eligible_for_dispute=True` within 90-day window |
| `test_ineligible_for_transactions_older_than_90_days` | `is_eligible_for_dispute=False` beyond 90 days |
| `test_ineligible_for_already_disputed_recent_transaction` | `is_eligible_for_dispute=False` when already disputed |
| `test_denormalizes_agent_into_complaint_row` | Agent name and type denormalized into complaint row |
| `test_latest_interaction_is_selected` | Most recent call interaction wins ROW_NUMBER deduplication |
| `test_no_agent_when_unassigned` | NULL agent fields when `assigned_agent_id` is NULL |
| `test_complaint_without_interaction_has_null_sentiment` | NULL sentiment when no interaction references the complaint |
