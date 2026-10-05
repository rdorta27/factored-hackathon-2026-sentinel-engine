---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Data Source Inventory — Sentinel Engine

**Version:** 1.0  
**Date:** 2026-10-01  
**Author:** Natalia Restrepo — Lead Data Engineer  
**Requirement:** REQ-0031 · Approved data, labeled by origin (P0)  
**Governing decision:** [ADR 023](build/decisions/023-pii-gold-handling.md)

---

## Compliance Declaration — REQ-0031

> **The Sentinel Engine operates only on the synthetic dataset in the official Factored Datathon 2026 S3 bucket. It adds internal evaluation fixtures that the team created.**
>
> The system uses no external real-world customer data, no web-scraped datasets, no production banking records and no unauthorized third-party data sources. This applies at each stage of the pipeline and of the LLM evaluation. Each dataset that the system consumes has a label for its origin, as REQ-0031 requires.

This document is the evidence artifact for REQ-0031. It closes the gap "Missing: the source inventory" that the requirements index noted. The [requirements index](requirements/requirements.md) holds the current status of each requirement. On 2026-10-05, REQ-0031, REQ-0014, REQ-0015 and REQ-0054 are all **Done**.

---

## 1. Data Source Inventory

The dataset snapshot ends on **2026-06-17** (`DATASET_CUTOFF_DATE`).

### 1.1 Organizer-Provided Tables (Factored Datathon 2026 S3 Bucket)

All 13 entities below are **fully synthetic**. The official problem statement declares it: *"no real customer information is included."* The pipeline reads them from the organizer S3 bucket. The bucket name is in `.env` (gitignored). The team never writes it to the repository.

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
| F-3 | Adversarial attack prompts | Team-crafted | Synthetic | 42 | Robustness testing; produced by `tests/adversarial/` in `sentinel-ai-core/` |

The team wrote all fixtures by hand. They hold no real names, no account numbers and no financial records.

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

These tables are the primary evidence for dispute resolution. Transactions feed `gold_dispute_eligible_transactions`. The pipeline joins customer attributes only at the Gold layer. It strips the credit score and the name fields before any data reaches the LLM.

### 2.2 Contact Center & Service

`complaints` · `service_agents` · `call_center_interactions` · `satisfaction_surveys` · `call_transcripts`

These tables give the escalation context and the conversation history. The AI core uses them to understand whether a customer already raised a dispute through the contact center.

### 2.3 Digital & Operational

`digital_events` · `branches` · `marketing_campaigns` · `campaign_sends`

These tables give behavioral and operational context. The pipeline uses them for the customer-360 enrichment in `gold_dispute_customer_360` and for eligibility heuristics.

### 2.4 Evaluation & Test Fixtures

The fixtures are the internal Spanish (`es-419`) and Portuguese (`pt-BR`) dispute scenarios and the adversarial prompts. Only the test suite in `sentinel-ai-core/tests/` consumes them. They never enter the data pipeline. Production runs do not load them into BigQuery or DuckDB.

---

## 3. Data Privacy & Synthetic Data Statement

### 3.1 Synthetic nature of the organizer dataset

The organizers generated the Factored Datathon 2026 dataset synthetically. The official problem statement says: *"no real customer information is included."* In detail:

- An algorithm generates the first and last names of the customers.
- The national identity numbers (CURP — Mexico; DNI — Argentina; CC — Colombia; CPF — Brazil) are fictitious.
- The addresses, phone numbers and email addresses are artificial.
- The credit scores come from statistical distributions. They do not come from credit bureaus.
- The transaction amounts, merchant names and timestamps are procedurally generated. They are statistically plausible. They do not come from any real financial event.

### 3.2 PII enforcement at the Gold layer

The upstream synthetic data was never real PII. Even so, the pipeline treats the fields that *structurally resemble* PII as sensitive. It removes them before any data reaches the LLM layer. **ADR 023** governs this (`docs/build/decisions/023-pii-gold-handling.md`).

The view `v_service_dispute_eligible_transactions` is the **only surface** that `sentinel-ai-core` can read. It drops these columns:

| Dropped column | Reason |
|---|---|
| `customer_first_name` | Structurally PII — not needed for dispute eligibility |
| `customer_last_name` | Structurally PII — not needed for dispute eligibility |
| `customer_credit_score` | Sensitive financial attribute — not relevant to inquiry resolution |

The view keeps all other columns of `gold_dispute_eligible_transactions` only if they carry no PII signal.

### 3.3 No external data

The system does **not** use these data sources. REQ-0031 prohibits them:

- Public banking datasets (for example, the CFPB complaint database and Kaggle banking datasets)
- Web-scraped customer reviews or social media data
- Third-party credit bureau feeds
- Any real institution's transaction exports
- LLM training corpora used as structured data

---

## 4. Requirement Traceability

| Requirement | Status on 2026-10-05 | Notes |
|---|---|---|
| REQ-0031 — Approved data, labeled by origin | **Done** | This document is the evidence artifact |
| REQ-0015 — Repeatable pipeline | **Done** | REQ-0031 unblocked it |
| REQ-0014 — Analytics data-backed problem | **Done** | REQ-0031 unblocked it |
| REQ-0054 — Justified external data | **Done** | The system uses no external data. The absence satisfies the requirement |
| ADR 023 — PII Gold handling | Implemented | `v_service_dispute_eligible_transactions` is live |
