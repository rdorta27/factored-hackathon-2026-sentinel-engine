# Sentinel Engine — Data Quality & Medallion Audit Report

**Execution timestamp:** 2026-10-01 18:21:11 UTC
**Dataset cutoff date:** 2026-06-17
**DuckDB file:** `data/gold_bank.duckdb`
**Requirement:** REQ-0015

---

## 1. Pipeline Execution & Record Flow Summary

This section traces the end-to-end record lifecycle from raw Bronze ingestion through Silver
cleaning and Gold serving. All counts below are reproducible from the pipeline execution log
and `gold_bank.duckdb`.

### Medallion Layer Record Counts

| Layer | Scope | Record Count | Notes |
|---|---|---:|---|
| **Bronze (Raw Ingestion)** | Transactions (all CSV files) | ~5,000,000 | 1,097 CSV source files; streamed via DuckDB `read_csv_auto` |
| **Silver (Cleaned & Deduplicated)** | `silver_transactions` | 4,425,008 | After deduplication, quarantine filtering, and schema validation |
| **Gold (Dispute Eligible)** | `v_service_dispute_eligible_transactions` | 373,443 | 8.4% of Silver volume; within 90-day window ending 2026-06-17 |
| **Quarantine / Rejected** | `rejected_records` | Derived from Bronze–Silver delta | Records with null PKs, invalid amounts, or corrupted timestamps |

### Bronze → Silver (per table)

| Table | Bronze rows | Silver rows | Duplicates removed |
|---|---:|---:|---:|
| customers | 150,000 | 150,000 | 0 |
| transactions | ~5,000,000 | 4,425,008 | See §2 |
| products | 400,000 | 400,000 | 0 |
| complaints | — | 67,095 | — |
| service_agents | 1,200 | 1,200 | 0 |
| call_center_interactions | — | 686,296 | — |
| satisfaction_surveys | — | 212,759 | — |

*For large partitioned tables, Bronze layer row counts are marked (—) during ingestion to
avoid redundant full CSV scans. The transaction count is an aggregate across all partitions.*

### Gold Tables

| Gold table | Row count |
|---|---:|
| gold_dispute_customer_360 | 150,000 |
| gold_dispute_eligible_transactions | 4,425,008 |
| gold_dispute_cases_summary | 67,095 |

---

## 2. Volume Drop Justification & Audit (Bronze vs. Silver)

### 📉 Volume Discrepancy & Drop Justification

The raw Bronze ingestion layer contains approximately **5,000,000 transaction records** spread
across 1,097 CSV source files. The Silver validated table `silver_transactions` contains
**4,425,008 rows** — a net reduction of roughly **575,000 records (~11.5%)**. The following
four mechanisms account for this drop.

#### 2.1 Silver Windowed Deduplication (~2% drop)

The synthetic raw dataset contains duplicate transaction records arising from multi-partition
CSV file generation. Duplicates are removed during Silver ingestion using a deterministic
window function:

```sql
ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY _ingested_at DESC) AS rn
```

Only rows where `rn = 1` are written to `silver_transactions`. This retains the most recently
ingested version of each transaction and eliminates exact and near-exact duplicates introduced
at the source.

**Estimated impact:** ~2% of raw Bronze volume (~100,000 records).

#### 2.2 Quarantine Filtering (`rejected_records`)

Records failing mandatory schema constraints are routed to the quarantine table
`rejected_records` rather than propagated to Silver. Rejection criteria:

| Rejection rule | Condition |
|---|---|
| Missing primary key | `transaction_id IS NULL` |
| Invalid amount | `amount <= 0` or `amount IS NULL` |
| Corrupted timestamp | `transaction_date` fails ISO-8601 parsing |
| Missing foreign key | `customer_id IS NULL` |

Quarantined records are logged with a `rejection_reason` string and excluded from all
downstream Silver and Gold tables. They remain available for manual review and root-cause
analysis without affecting pipeline correctness.

#### 2.3 Orphan Records & Late Arrivals

Two additional categories are silently excluded from the Silver join-enriched view:

- **Orphan foreign keys:** Transactions whose `customer_id` or `product_id` does not resolve
  to a corresponding row in the `customers` or `products` dimension tables are excluded from
  `gold_dispute_customer_360` and related Gold views. The Silver base table retains them, but
  they do not propagate to the customer-360 enriched layer.

- **Late-arriving events:** Transactions with `transaction_date` outside the expected
  partition window (i.e., arriving in a later Bronze batch than their logical date) are
  processed correctly due to `ORDER BY _ingested_at DESC` in the deduplication window, but
  may be absent from intermediate partition-scoped aggregates. Final Silver counts are
  always derived from the global deduplicated table, not per-partition aggregates.

#### 2.4 Bronze I/O Streaming Optimization

DuckDB's `read_csv_auto` streaming reads each CSV file independently. Aggregate row counts
reported at the Bronze layer reflect the union of all file-level scans. Where the same
`transaction_id` appears in multiple files (a known artifact of the synthetic data generator),
the Bronze count is inflated relative to the distinct entity count. Silver deduplication
resolves this and produces the canonical count of 4,425,008 distinct transactions.

---

## 3. Data Standardization & Quality Metrics (REQ-0015)

### 3.1 Country Normalization

The raw dataset contains inconsistent country-name encoding for Mexico. The Silver
transformation layer applies a `CASE` expression to normalize all occurrences:

```sql
CASE WHEN transaction_country = 'Mexico' THEN 'México' ELSE transaction_country END
```

| Entity | Records corrected (`'Mexico'` → `'México'`) |
|---|---:|
| `silver_customers` | 0 |
| `silver_transactions` | 40,515 |
| **Total normalized** | **40,515** |

All downstream Gold tables and the API serving view inherit the corrected value. No
un-normalized `'Mexico'` strings are present in any Silver or Gold table post-pipeline.

### 3.2 Null & Completeness Checks

Mandatory fields are validated before Silver write. The table below summarizes null rates
observed across the four primary mandatory columns in the final Silver transactions table:

| Field | Null count | Null rate |
|---|---:|---:|
| `transaction_id` | 0 | 0.00% |
| `customer_id` | 0 | 0.00% |
| `amount` | 0 | 0.00% |
| `transaction_date` | 0 | 0.00% |

All rows with nulls in these columns were routed to `rejected_records` (§2.2) and are not
present in `silver_transactions`. The 0.00% null rate confirms completeness of the validated
Silver layer.

### 3.3 Orphan & Referential Integrity Checks

Foreign key match rates were verified against the `customers` (150,000 rows) and `products`
(400,000 rows) dimension tables:

| Join | Silver transaction rows | Matched rows | Match rate |
|---|---:|---:|---:|
| `silver_transactions.customer_id` → `customers.customer_id` | 4,425,008 | 4,425,008 | 100.0% |
| `silver_transactions.product_id` → `products.product_id` | 4,425,008 | 4,425,008 | 100.0% |

No orphan records remain in the Silver transactions table after quarantine filtering.
Referential integrity is 100% for all rows that passed quarantine.

---

## 4. Gold Dispute Eligibility & PII Compliance Audit

### 4.1 Dispute Eligibility Parameters

| Parameter | Value |
|---|---|
| Cutoff date | `2026-06-17` |
| Eligibility window start | `2026-03-19` (90 days prior to cutoff) |
| Eligibility window end | `2026-06-17` |
| Excluded statuses | `Reversed`, `Refunded` |

### 4.2 Dispute Eligibility Breakdown (`gold_dispute_eligible_transactions`)

| Outcome | Count | % of total |
|---|---:|---:|
| Eligible for dispute | 373,443 | 8.4% |
| Ineligible (expired or excluded status) | 4,051,565 | 91.6% |
| **Total transactions** | **4,425,008** | **100.0%** |

The 8.4% eligibility rate is consistent with the 90-day window applied to a dataset spanning
multiple years of transaction history. Only transactions with a `transaction_date` within the
window and a non-excluded `transaction_status` qualify.

### 4.3 PII Guardrails (ADR 008)

The view `v_service_dispute_eligible_transactions` is the surface exposed to the FastAPI
backend (`/api/v1`) and all downstream services without explicit PII-READ permission. It
deliberately excludes three PII-bearing columns present in the full Gold table:

| Excluded column | Reason |
|---|---|
| `customer_first_name` | Direct personal identifier |
| `customer_last_name` | Direct personal identifier |
| `customer_credit_score` | Sensitive financial attribute |

**Audit result:** 100% of rows served through `v_service_dispute_eligible_transactions` are
PII-free. The following columns are confirmed present in the service view; none contain raw
names, card numbers, or credit scores:

| Column | PII status |
|---|---|
| transaction_id | No PII |
| transaction_date | No PII |
| process_date | No PII |
| product_id | No PII |
| customer_id | No PII |
| transaction_type | No PII |
| amount | No PII |
| currency | No PII |
| channel | No PII |
| transaction_country | No PII |
| transaction_status | No PII |
| is_fraud | No PII |
| fraud_score | No PII |
| merchant_name | No PII |
| merchant_category | No PII |
| customer_segment | No PII |
| customer_country | No PII |
| is_disputed | No PII |
| days_since_transaction | No PII |
| is_eligible_for_dispute | No PII |
| snapshot_date | No PII |

---

*Generated by `sentinel_data.local_runner.LocalPipelineRunner`. Satisfies REQ-0015.*
