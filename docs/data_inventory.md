# Data Source Inventory — Sentinel Engine

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Natalia Restrepo — Lead Data Engineer  
**Requirement:** REQ-0031 · Approved data, labeled by origin (P0)  
**Governing decision:** [ADR 023](build/decisions/023-pii-gold-handling.md)

---

## Compliance Declaration — REQ-0031

> **The Sentinel Engine operates exclusively on the synthetic dataset provided in the official Factored Datathon 2026 S3 bucket, supplemented by internal evaluation fixtures created by the team.**
>
> No external real-world customer data, web-scraped datasets, production banking records, or unauthorized third-party data sources are used at any stage of the pipeline or LLM evaluation. Every dataset consumed by this system is labeled by origin as required by REQ-0031.

This document is the evidence artifact that satisfies the "Missing: the source inventory" gap noted in the requirements index. Once merged, REQ-0031 moves from **Pending** to **Done** and unblocks REQ-0015, REQ-0017, REQ-0020, REQ-0014, and REQ-0054.

---

## 1. Data Source Inventory

Dataset snapshot cutoff: **2026-06-17** (`DATASET_CUTOFF_DATE`).

### 1.1 Organizer-Provided Tables (Factored Datathon 2026 S3 Bucket)

All 13 entities below are **fully synthetic** as declared in the official problem statement: *"no real customer information is included."* They are read from the organizer S3 bucket; the bucket name is stored in `.env` (gitignored) and is never written to the repository.

| # | Entity / Table | Type | Approx. Rows | Business Domain | Purpose |
|---|---|---|---|---|---|
| 1 | `customers` | Dimension | 150,000 | Core Banking | Customer master: demographics, credit score, country of residence |
| 2 | `products` | Dimension | 400,000 | Core Banking | Product catalog: cards, loans, accounts |
| 3 | `branches` | Dimension | 350 | Operations | Physical branch locations |
| 4 | `service_agents` | Dimension | 1,200 | Contact Center | Agent roster: skills, tenure, channel |
| 5 | `marketing_campaigns` | Dimension | 200 | Marketing | Campaign metadata |
| 6 | `transactions` | Fact | 5,000,000 | Core Banking | Card and account transactions; primary dispute evidence |
| 7 | `call_center_interactions` | Fact | 800,000 | Contact Center | Contact events: channel, queue, resolution code |
| 8 | `call_transcripts` | Fact | 200,000 | Contact Center | Free-text transcripts of agent–customer calls |
| 9 | `satisfaction_surveys` | Fact | 250,000 | Contact Center | Post-contact NPS and CSAT scores |
| 10 | `digital_events` | Fact | 10,000,000 | Digital | App and web clickstream |
| 11 | `complaints` | Fact | 80,000 | Service Escalation | Formal complaint records; maps to dispute eligibility |
| 12 | `campaign_sends` | Fact | 2,000,000 | Marketing | Campaign send log per customer |
| 13 | `daily_exchange_rates` | Reference | 3,000 | Operations | FX rates used for multi-currency transaction normalization |

### 1.2 Internal Team Fixtures

| # | Fixture | Origin | Data Nature | Approx. Cases | Purpose |
|---|---|---|---|---|---|
| F-1 | Dispute test cases — Spanish | Team-crafted | Synthetic / anonymized mock | ~200 | LLM policy evaluation in `es-419` (Latin American Spanish) |
| F-2 | Dispute test cases — Portuguese | Team-crafted | Synthetic / anonymized mock | ~200 | LLM policy evaluation in `pt-BR` |
| F-3 | Adversarial attack prompts | Team-crafted | Synthetic | ~50 | Robustness testing; produced by `tests/adversarial/` in `sentinel-ai-core/` |

All fixtures are hand-crafted by the team; no real names, account numbers, or financial records appear in them.

---

## 2. Domain Categorization and Pipeline Lineage

```
S3 Bucket (organizer)
    │
    ▼ Bronze layer (raw ingest, schema-enforced)
    │
    ▼ Silver layer (cleaned, typed, normalized — PII retained for traceability)
    │
    ├─ silver_customers          ← customers (canonical country names, REQ-0015)
    ├─ silver_transactions       ← transactions
    ├─ silver_complaints         ← complaints
    ├─ silver_call_center_interactions
    ├─ silver_call_transcripts
    ├─ silver_satisfaction_surveys
    ├─ silver_digital_events
    ├─ silver_branches
    ├─ silver_service_agents
    ├─ silver_marketing_campaigns
    ├─ silver_campaign_sends
    └─ silver_daily_exchange_rates
    │
    ▼ Gold layer (business-ready aggregates)
    │
    ├─ gold_dispute_customer_360         (~150,000 rows)
    ├─ gold_dispute_eligible_transactions (~5,000,000 rows)
    ├─ gold_dispute_cases_summary        (~80,000 rows)
    └─ v_service_dispute_eligible_transactions  ← PII-free view (ADR 023)
```

### 2.1 Core Banking & Accounts

`customers` · `transactions` · `products` · `daily_exchange_rates`

The primary dispute-resolution evidence. Transactions feed `gold_dispute_eligible_transactions`. Customer attributes are joined only at the Gold layer, and credit score and name fields are stripped before any data reaches the LLM.

### 2.2 Contact Center & Service

`complaints` · `service_agents` · `call_center_interactions` · `satisfaction_surveys` · `call_transcripts`

Provides the escalation context and conversation history that the AI core uses to understand whether a customer has already raised a dispute through the contact center.

### 2.3 Digital & Operational

`digital_events` · `branches` · `marketing_campaigns` · `campaign_sends`

Behavioral and operational context. Used for customer-360 enrichment in `gold_dispute_customer_360` and for eligibility heuristics.

### 2.4 Evaluation & Test Fixtures

Internal Spanish (`es-419`) and Portuguese (`pt-BR`) dispute scenarios and adversarial prompts. These are consumed only by the test suite in `sentinel-ai-core/tests/`; they never enter the data pipeline and are not loaded into BigQuery or DuckDB in production runs.

---

## 3. Data Privacy & Synthetic Data Statement

### 3.1 Synthetic nature of the organizer dataset

The Factored Datathon 2026 dataset was generated synthetically. According to the official problem statement, *"no real customer information is included."* Specifically:

- Customer first and last names are algorithmically generated.
- National identity numbers (CURP — Mexico; DNI — Argentina; CC — Colombia; CPF — Brazil) are fictitious.
- Addresses, phone numbers, and email addresses are artificial.
- Credit scores are drawn from statistical distributions, not sourced from credit bureaus.
- Transaction amounts, merchant names, and timestamps are procedurally generated to be statistically plausible but are not derived from any real financial event.

### 3.2 PII enforcement at the Gold layer

Even though the upstream synthetic data was never real PII, the pipeline treats the fields that *structurally resemble* PII as sensitive and enforces their removal before any data reaches the LLM layer. This is governed by **ADR 023** (`docs/build/decisions/023-pii-gold-handling.md`).

The view `v_service_dispute_eligible_transactions` is the **only surface** exposed to `sentinel-ai-core`. It explicitly drops:

| Dropped column | Reason |
|---|---|
| `customer_first_name` | Structurally PII — not needed for dispute eligibility |
| `customer_last_name` | Structurally PII — not needed for dispute eligibility |
| `customer_credit_score` | Sensitive financial attribute — not relevant to inquiry resolution |

All other columns in `gold_dispute_eligible_transactions` are retained in the view only if they carry no PII signal.

### 3.3 No external data

The following data sources are explicitly **not used** and are prohibited by REQ-0031:

- Public banking datasets (e.g., CFPB complaint database, Kaggle banking datasets)
- Web-scraped customer reviews or social media data
- Third-party credit bureau feeds
- Any real institution's transaction exports
- LLM training corpora used as structured data

---

## 4. Requirement Traceability

| Requirement | Status after this document | Notes |
|---|---|---|
| REQ-0031 — Approved data, labeled by origin | **Done** | This document is the evidence artifact |
| REQ-0015 — Repeatable pipeline | In progress | Unblocked by REQ-0031 |
| REQ-0014 — Analytics data-backed problem | In progress | Unblocked by REQ-0031 |
| REQ-0054 — Justified external data | Pending | No external data used; requirement is satisfied by absence |
| ADR 023 — PII Gold handling | Implemented | `v_service_dispute_eligible_transactions` is live |
