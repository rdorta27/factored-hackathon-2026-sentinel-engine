# Sizing & Capacity Specification — Sentinel Engine

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Natalia Restrepo — Lead Data Engineer  
**Requirement:** REQ-0053 · Sizing and capacity plan  
**Related decisions:** [ADR 001](build/decisions/001-azure-platform.md) · [ADR 005](build/decisions/005-backend.md)

---

## 1. Executive Summary

This document specifies the operational workload, dispute volume projections, local prototype performance benchmarks, and production scaling roadmap for the Sentinel Engine dispute-resolution system.

Sizing scope covers four layers:

1. **Historical transaction volume** — the empirical dataset used to validate pipeline and model correctness.
2. **Dispute frequency** — daily and peak rates derived from the 90-day dataset window ending at the 2026-06-17 cutoff.
3. **Local DuckDB prototype throughput** — measured on a single developer machine to set the performance baseline.
4. **Azure cloud scaling targets** — the architecture and SLO targets for a regional bank deployment.

All workload numbers below are grounded in the Medallion pipeline run executed against the Factored Datathon 2026 synthetic dataset. No production bank data is used; sizing ratios are the analytically valid output.

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

The Gold view `v_service_dispute_eligible_transactions` applies the eligibility filter (transaction age ≤ 90 days relative to the 2026-06-17 cutoff, status not already resolved, product type eligible for dispute).

| Metric | Value | Derivation |
|---|---|---|
| Eligible transactions (90-day window) | **373,443** | Direct query on `gold_dispute_eligible_transactions` |
| Eligibility rate | **8.4%** | 373,443 / 4,420,000 |
| Historical formal complaints (90-day window) | **251** | `silver_complaints` filtered to window |
| Formal disputes filed per calendar day (avg) | **~3 / day** | 251 / 90 days |

### 2.3 Daily Inquiry Load

Customers who call the contact center to inquire about a transaction before filing a formal dispute represent approximately 35% of total call center volume in the dataset.

| Metric | Value | Derivation |
|---|---|---|
| Total call center interactions (90-day window) | ~54,900 | `silver_call_center_interactions` |
| Dispute-related inquiry share | ~35% | Complaints-to-interaction ratio |
| Average dispute inquiry calls per day | **~213 / day** | 0.35 × 54,900 / 90 |

Each inquiry triggers one Sentinel AI Core `/api/v1/chat` request. At steady state, the system must sustain **~213 requests/day (~0.15 req/s)** with end-to-end response times inside the targets of section 4.3.

### 2.4 Peak Workload Projections

High-volume commercial events (Hot Sale, CyberMonday, end-of-month billing cycles) produce transaction spikes that translate into dispute spikes 24–72 hours later.

| Scenario | Formal Disputes | Inquiry Calls | Chat API Req/s |
|---|---|---|---|
| Steady state (avg) | ~3 / day | ~213 / day | ~0.15 |
| Moderate peak (weekday billing cycle) | ~8 / day | ~500 / day | ~0.35 |
| High-volume event (Hot Sale / CyberMonday) | **15–20 / day** | **~1,000 / day** | **~0.70** |
| Stress ceiling (10× steady state) | ~30 / day | ~2,100 / day | ~1.5 |

The stress ceiling represents the design target for auto-scaling: the system must handle a 10× burst without service degradation and return to steady-state resource usage within 5 minutes of the peak subsiding.

---

## 3. Local Prototype Capacity & Performance Benchmarks

These measurements are from a single developer machine (Linux / WSL2) running the full Medallion pipeline end-to-end.

### 3.1 Data Processing Engine — DuckDB

| Metric | Measured Value |
|---|---|
| Raw source files | 1,097 CSV files |
| Total raw records ingested | ~19,000,000 |
| End-to-end pipeline duration (Bronze → Silver → Gold) | **~10 minutes** |
| Resulting database file | `gold_bank.duckdb` — **652 MB** |
| Peak memory (DuckDB in-process) | < 4 GB |

DuckDB's columnar execution engine processes all 13 source tables in a single-node, in-process model. No external server, no network I/O, and no serialization overhead between layers.

### 3.2 Service Layer Query Latency

The PII-free Gold view `v_service_dispute_eligible_transactions` is the read surface exposed to `sentinel-ai-core`. Candidate transaction lookups are point queries filtered by `customer_id` and date range.

| Query type | p50 latency | p99 latency |
|---|---|---|
| Single-customer eligible transactions | < 10 ms | < 50 ms |
| Dispute eligibility check (single `transaction_id`) | < 5 ms | < 20 ms |
| Customer 360 profile fetch (`gold_dispute_customer_360`) | < 15 ms | < 50 ms |

**Design target for the service layer: < 50 ms** for any Gold view read, leaving the remaining budget for LLM inference and API serialization.

### 3.3 Operational Dispute Store — SQLite (Prototype)

The prototype uses an isolated SQLite database for the dispute operational record. It enforces idempotency via unique constraints on `(dispute_id, transaction_id)`.

| Metric | Value |
|---|---|
| Write latency (single dispute insert) | < 2 ms |
| Idempotency constraint | `UNIQUE(dispute_id, transaction_id)` |
| Concurrent writer support | Single-process only (SQLite limitation) |
| Max safe throughput | ~50 writes/s |

The SQLite store is adequate for the prototype and local demo. It is replaced in production (see Section 4.2).

---

## 4. Production Scaling Strategy — Azure Cloud Architecture

The local prototype validates correctness. The following architecture replaces each local component for a multi-tenant, multi-region bank deployment.

### 4.1 Data Lakehouse — Azure Databricks + Delta Lake

| Prototype | Production replacement |
|---|---|
| DuckDB single-node in-process | **Azure Databricks (PySpark + Delta Lake on ADLS Gen2)** |
| Manual full-reload pipeline | **Delta Auto Loader** (continuous incremental ingestion via `cloudFiles`) |
| Local CSV source | **ADLS Gen2 landing zone** (bank's nightly extracts or CDC streams) |
| Local DuckDB Gold tables | **Delta tables in Unity Catalog** (versioned, auditable, ACID) |

**Cluster sizing (initial production target):**

| Tier | Worker nodes | vCores / node | RAM / node | Use case |
|---|---|---|---|---|
| Daily batch | 4 workers | 8 vCores | 32 GB | Full Silver + Gold refresh |
| Incremental (streaming) | 2 workers | 4 vCores | 16 GB | Auto Loader micro-batch |
| Ad-hoc query | 1 worker (autoscale to 4) | 8 vCores | 32 GB | Analyst queries, evidence runs |

Delta Auto Loader enables sub-minute latency from source file arrival to Gold view availability, replacing the current ~10-minute full-pipeline run.

### 4.2 Operational Store — Azure Database for PostgreSQL (Flexible Server)

| Prototype | Production replacement |
|---|---|
| SQLite (single-process) | **Azure Database for PostgreSQL — Flexible Server** |
| `UNIQUE(dispute_id, transaction_id)` in SQLite | Same constraint, enforced at DB level with row-level locking |
| ~50 writes/s max | **> 10,000 writes/s** (General Purpose, 8 vCores) |
| No HA | **Zone-redundant HA** with automatic failover < 30 s |

PostgreSQL supports concurrent writes from multiple FastAPI replicas without serialization. The `disputes` table schema is identical to the prototype; only the connection string changes.

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

The model targets come from the measured router latency, not from an estimate. The router runs **first** on every text turn: it labels the intent before the loop reads Gold or checks eligibility. A turn that selects a charge from the list (a structured candidate id) does not call the model. The non-LLM path (eligibility check, customer lookup, idempotency gate) must complete in < 200 ms at p95 under peak load (1,000 inquiry calls/day ≈ 0.70 req/s sustained). These numbers are not a load test of `/api/v1/chat`: that test is still open.

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
| REQ-0015 | Repeatable pipeline | In progress | Unblocked by REQ-0031 |
| REQ-0031 | Approved data, labeled by origin | Done | `docs/data_inventory.md` |
| ADR 001 | Azure platform | Implemented | Databricks + Container Apps target |
| ADR 005 | Python + FastAPI backend | Implemented | Container Apps deployment model |
| ADR 023 | PII Gold handling | Implemented | `v_service_dispute_eligible_transactions` |

### 5.1 Sizing Completeness Checklist

- [x] Baseline transaction and customer volumes documented from the pipeline run
- [x] Eligible dispute volume quantified (373,443 transactions, 8.4% eligibility rate)
- [x] Daily average formal dispute rate derived from empirical complaint data (~3/day)
- [x] Daily average inquiry load derived from call center data (~213/day)
- [x] Peak workload projections defined (Hot Sale / CyberMonday: 15–20 disputes/day, ~1,000 calls/day)
- [x] Local prototype benchmarks measured (19M records, ~10 min pipeline, < 50 ms query latency)
- [x] Production data lakehouse architecture specified (Databricks + Delta Lake + Auto Loader)
- [x] Production operational store specified (Azure PostgreSQL — Flexible Server)
- [x] Production serving layer specified (Azure Container Apps + KEDA auto-scaling)
- [x] Latency SLOs defined for non-LLM and LLM paths
- [x] Storage tiers and retention periods defined
