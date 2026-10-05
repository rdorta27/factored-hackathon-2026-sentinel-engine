---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Sizing & Capacity Specification — Sentinel Engine

**Version:** 1.0  
**Date:** 2026-10-05  
**Author:** Natalia Restrepo — Lead Data Engineer  
**Requirement:** REQ-0053 · Sizing and capacity plan  
**Related decisions:** [ADR 001](build/decisions/001-azure-platform.md) · [ADR 005](build/decisions/005-backend.md)

---

## 1. Executive Summary

This document specifies four items for the Sentinel Engine dispute-resolution system: the operational workload, the projections of dispute volume, the performance benchmarks of the local prototype and the production scaling roadmap.

The sizing covers four layers:

1. **Historical transaction volume.** This is the empirical dataset that validates the correctness of the pipeline and the models.
2. **Dispute frequency.** The daily rates and the peak rates come from the 90-day dataset window that ends at the cutoff of 2026-06-17.
3. **Throughput of the local DuckDB prototype.** The team measured it on one developer machine to set the performance baseline.
4. **Azure cloud scaling targets.** These are the architecture and the SLO targets for a regional bank deployment.

All workload numbers below come from the Medallion pipeline run on the Factored Datathon 2026 synthetic dataset. The team used no production bank data. The sizing ratios are the analytically valid output.

---

## 2. Dispute Volume & Workload Sizing

### 2.1 Dataset Baseline

| Metric | Value | Source |
|---|---|---|
| Total transactions ingested | ~5,000,000 | `catalog.py` · `approximate_rows` |
| Total customers | 150,000 | `catalog.py` |
| Dataset snapshot cutoff | 2026-06-17 | `DATASET_CUTOFF_DATE` |
| Transactions processed in pipeline run | ~4,420,000 | Medallion pipeline run |
| Database file size (local) | 652 MB | `gold_bank.duckdb` |

### 2.2 Eligible Dispute Volume (90-Day Window)

The Gold view `v_service_dispute_eligible_transactions` applies the eligibility filter. A transaction is eligible when it meets three conditions:

- The transaction is 90 days old or less, relative to the cutoff of 2026-06-17.
- The status is not already resolved.
- The product type is eligible for dispute.

| Metric | Value | Derivation |
|---|---|---|
| Eligible transactions (90-day window) | **373,443** | Direct query on `gold_dispute_eligible_transactions` |
| Eligibility rate | **8.4%** | 373,443 / 4,420,000 |
| Historical formal complaints (90-day window) | **251** | `silver_complaints` filtered to window |
| Formal disputes filed per calendar day (avg) | **~3 / day** | 251 / 90 days |

### 2.3 Daily Inquiry Load

Some customers call the contact center to ask about a transaction before they file a formal dispute. They are about 35% of the total call center volume in the dataset.

| Metric | Value | Derivation |
|---|---|---|
| Total call center interactions (90-day window) | ~54,900 | `silver_call_center_interactions` |
| Dispute-related inquiry share | ~35% | Complaints-to-interaction ratio |
| Average account-inquiry calls per day | **218.48 / day** | [`problem/dev-v1`](../evidence/problem/dev-v1/summary.json): `demand.account_or_payment_inquiry.per_day_mean` |
| Busy day (p95) | **292 / day** | `demand.account_or_payment_inquiry.busy_day_p95` |
| Highest day | **332 / day** | `demand.account_or_payment_inquiry.highest_day` |

Each inquiry triggers one Sentinel AI Core `/api/v1/chat` request. At steady state, the system must sustain **~218 requests/day**. The end-to-end response times must stay inside the targets of section 4.3.

### 2.4 Peak Workload

The problem run measures the calls a day on the development zone ([`problem/dev-v1`](../evidence/problem/dev-v1/summary.json), event dates 2023-06-17 to 2025-07-01). A busy day is the 95th percentile of the daily counts: 95 of 100 days are below it. The highest day is the maximum.

| Workload | Mean a day | Busy day (p95) | Highest day | Source |
|---|---|---|---|---|
| Account inquiry (flow entry) | 218.48 | 292 [289, 296] | 332 [316, 332] | `demand.account_or_payment_inquiry.*` |
| Transaction dispute | 106.3 | 145 [142, 148] | 169 [162, 169] | `demand.transaction_dispute.*` |

The scenarios below are **projections**. The dataset has no campaign calendar, so the team cannot measure a commercial event. Each row multiplies the measured busy day by an assumed event factor.

| Scenario | Formal Disputes | Inquiry Calls | Chat API Req/s |
|---|---|---|---|
| Busy day (measured) | — | 292 / day | ~0.20 |
| Moderate peak (weekday billing cycle) | ~8 / day | ~500 / day | ~0.35 |
| High-volume event (Hot Sale / CyberMonday) | **15–20 / day** | **~1,000 / day** | **~0.70** |
| Stress ceiling (10× steady state) | ~30 / day | ~2,100 / day | ~1.5 |

The stress ceiling is the design target for auto-scaling. The system must handle a 10× burst with no service degradation. It must return to steady-state resource usage within 5 minutes after the peak ends. The formal-dispute counts stay projections. The dataset does not separate dispute calls from other account inquiries.

---

## 3. Local Prototype Capacity & Performance Benchmarks

The team made these measurements on one developer machine (Linux / WSL2). The machine ran the full Medallion pipeline from start to end.

### 3.1 Data Processing Engine — DuckDB

| Metric | Measured Value |
|---|---|
| Raw source files | 1,097 CSV files |
| Total raw records ingested | ~19,000,000 |
| End-to-end pipeline duration (Bronze → Silver → Gold) | **~10 minutes** |
| Resulting database file | `gold_bank.duckdb` — **652 MB** |
| Peak memory (DuckDB in-process) | < 4 GB |

The columnar execution engine of DuckDB processes all 13 source tables in a single-node, in-process model. It needs no external server. It has no network I/O and no serialization overhead between layers.

### 3.2 Service Layer Query Latency

The PII-free Gold view `v_service_dispute_eligible_transactions` is the read surface for `sentinel-ai-core`. The candidate transaction lookups are point queries. They filter by `customer_id` and date range.

| Query type | p50 latency | p99 latency |
|---|---|---|
| Single-customer eligible transactions | < 10 ms | < 50 ms |
| Dispute eligibility check (single `transaction_id`) | < 5 ms | < 20 ms |
| Customer 360 profile fetch (`gold_dispute_customer_360`) | < 15 ms | < 50 ms |

**Design target for the service layer: < 50 ms** for any Gold view read. The rest of the budget is for LLM inference and API serialization.

### 3.3 Operational Dispute Store — SQLite (Prototype)

The prototype uses an isolated SQLite database for the operational record of the disputes. Unique constraints on `(dispute_id, transaction_id)` enforce idempotency.

| Metric | Value |
|---|---|
| Write latency (single dispute insert) | < 2 ms |
| Idempotency constraint | `UNIQUE(dispute_id, transaction_id)` |
| Concurrent writer support | Single-process only (SQLite limitation) |
| Max safe throughput | ~50 writes/s |

The SQLite store is adequate for the prototype and the local demo. Production replaces it (see Section 4.2).

---

## 4. Production Scaling Strategy — Azure Cloud Architecture

The local prototype validates correctness. The architecture below replaces each local component for a multi-tenant, multi-region bank deployment.

### 4.1 Data Lakehouse — Azure Databricks + Delta Lake

| Prototype | Production replacement |
|---|---|
| DuckDB single-node in-process | **Azure Databricks (PySpark + Delta Lake on ADLS Gen2)** |
| Manual full-reload pipeline | **Delta Auto Loader** (continuous incremental ingestion via `cloudFiles`) |
| Local CSV source | **ADLS Gen2 landing zone** (nightly extracts or CDC streams of the bank) |
| Local DuckDB Gold tables | **Delta tables in Unity Catalog** (versioned, auditable, ACID) |

**Cluster sizing (initial production target):**

| Tier | Worker nodes | vCores / node | RAM / node | Use case |
|---|---|---|---|---|
| Daily batch | 4 workers | 8 vCores | 32 GB | Full Silver + Gold refresh |
| Incremental (streaming) | 2 workers | 4 vCores | 16 GB | Auto Loader micro-batch |
| Ad-hoc query | 1 worker (autoscale to 4) | 8 vCores | 32 GB | Analyst queries, evidence runs |

Delta Auto Loader gives sub-minute latency from the arrival of a source file to the availability of the Gold view. The current full-pipeline run takes ~10 minutes.

### 4.2 Operational Store — Azure Database for PostgreSQL (Flexible Server)

| Prototype | Production replacement |
|---|---|
| SQLite (single-process) | **Azure Database for PostgreSQL — Flexible Server** |
| `UNIQUE(dispute_id, transaction_id)` in SQLite | Same constraint, enforced at DB level with row-level locking |
| ~50 writes/s max | **> 10,000 writes/s** (General Purpose, 8 vCores) |
| No HA | **Zone-redundant HA** with automatic failover < 30 s |

PostgreSQL supports concurrent writes from many FastAPI replicas with no serialization. The schema of the `disputes` table is the same as in the prototype. Only the connection string changes.

### 4.3 Serving Layer — Azure Container Apps

| Prototype | Production replacement |
|---|---|
| Single FastAPI process (local) | **FastAPI on Azure Container Apps** |
| No auto-scaling | **HTTP-concurrency-based auto-scaling** (KEDA) |
| No TLS | **Azure Front Door** (TLS termination, WAF, DDoS) |
| No auth | **Azure AD B2C** (advisor authentication) |

**Auto-scaling rules:**

```
minReplicas: 1
maxReplicas: 20
trigger:
  type: http
  metadata:
    concurrentRequests: "10"   # scale-out when any replica serves > 10 concurrent requests
```

**Latency SLOs (production):**

| Percentile | Target | Scope |
|---|---|---|
| p50 | < 1.5 s | End-to-end `/api/v1/chat`, with one model call |
| p95 | < 5 s | End-to-end `/api/v1/chat`, with one model call |
| p95 | **< 200 ms** | Gold view query + API serialization (non-LLM path) |
| p99 | < 500 ms | Gold view query + API serialization (non-LLM path) |
| Model call (GLM 5.3 Flash on Fireworks AI, [016](build/decisions/016-router-models.md)) | measured p50 1079 ms, p95 4475 ms | [`2024Q4-eval-v7`](../evidence/evaluation-runs/2024Q4-eval-v7/summary.json): `component.versions.router_v2.latency_ms` |

The model targets come from the measured router latency. They are not an estimate. The router runs **first** on every text turn. It labels the intent before the loop reads Gold or checks eligibility. A turn that selects a charge from the list (a structured candidate id) does not call the model.

The non-LLM path (eligibility check, customer lookup, idempotency gate) must complete in < 200 ms at p95 under peak load (1,000 inquiry calls/day ≈ 0.70 req/s sustained). The load run [`20261005T211031Z`](../evidence/robustness/20261005T211031Z/summary.json) measures `/api/v1/chat` on one replica with recorded answers. At the deployed limits (0.5 vCPU, 1 GiB) the container reaches about 5 requests a second; the p95 rises to 918 ms at the target 20. The host serves 17.51 requests a second. The load test is done. The capacity page is [capacity and latency](rationale/capacity-and-latency.md).

### 4.4 Storage & Retention

| Data tier | Storage | Retention | Access pattern |
|---|---|---|---|
| Bronze (raw CSVs / CDC) | ADLS Gen2 — Hot tier | 90 days | Write-once, batch read |
| Silver (cleaned Delta) | ADLS Gen2 — Hot tier | 1 year | Daily batch + incremental |
| Gold (serving Delta) | ADLS Gen2 — Hot tier | 1 year | Low-latency point queries |
| Gold view (PII-free) | Databricks SQL Warehouse | Derived | Sub-second queries from API |
| Operational disputes (PostgreSQL) | Azure DB for PostgreSQL | Indefinite | OLTP — read/write |
| Audit log | Azure Monitor / Log Analytics | 7 years | Append-only, compliance |

---

## 5. Requirement Traceability

| Requirement | Description | Status | Evidence |
|---|---|---|---|
| REQ-0053 | Sizing and capacity plan | **Done** | This document |
| REQ-0015 | Repeatable pipeline | **Done** | REQ-0031 unblocked it |
| REQ-0031 | Approved data, labeled by origin | Done | `docs/data_inventory.md` |
| ADR 001 | Azure platform | Implemented | Databricks + Container Apps target |
| ADR 005 | Python + FastAPI backend | Implemented | Container Apps deployment model |
| ADR 023 | PII Gold handling | Implemented | `v_service_dispute_eligible_transactions` |

### 5.1 Sizing Completeness Checklist

- [x] Baseline transaction and customer volumes documented from the pipeline run
- [x] Eligible dispute volume quantified (373,443 transactions, 8.4% eligibility rate)
- [x] Daily average formal dispute rate derived from empirical complaint data (~3/day)
- [x] Daily average inquiry load measured on the development zone (218.48/day, busy day 292, highest day 332; [`problem/dev-v1`](../evidence/problem/dev-v1/summary.json))
- [x] Peak workload projections defined (Hot Sale / CyberMonday: 15–20 disputes/day, ~1,000 calls/day), labelled as projections
- [x] Local prototype benchmarks measured (19M records, ~10 min pipeline, < 50 ms query latency)
- [x] Production data lakehouse architecture specified (Databricks + Delta Lake + Auto Loader)
- [x] Production operational store specified (Azure PostgreSQL — Flexible Server)
- [x] Production serving layer specified (Azure Container Apps + KEDA auto-scaling)
- [x] Latency SLOs defined for non-LLM and LLM paths
- [x] Storage tiers and retention periods defined
