# Flow options

The four options from the original brief, with a suggested stack. The current proposal is the transaction-dispute flow: see [decision 003](../decisions/003-disputes-flow.md).

**Purpose:** input to the flow decision. **Status:** proposal reviewed against the original brief, the kickoff, the dataset overview, and the dictionary. **Related:** [dataset](../../understand/dataset.md), [requirements](../../requirements/requirements.md), [ML](../areas/ml.md).

Sources: *brief* (Scope: account or payment inquiries, card-service support, transaction-dispute intake, credit-product information and eligibility support), *kickoff p. 10*, *dataset overview*, *dictionary*.

## Common constraints

- **Team:** 3 people, delivery on Monday 10/5 (official 10-day sprint starting 9/25). We choose **one** coherent flow; per the brief, the options are examples, not separate categories, and implementing more flows earns no automatic bonus.
- **Small backend on Azure (suggested base stack, aligned with [decision 001](../decisions/001-azure-platform.md)):**
  - Data: Parquet + local **DuckDB** for development; deployment on Azure. The 19M rows fit on a laptop for exploration.
  - API: **FastAPI** with mock bank tools (documented contracts) and a signed test session (JWT) for authentication.
  - Retrieval: open-source multilingual embeddings (`multilingual-e5-small`) stored in DuckDB or FAISS.
  - LLM: **Azure OpenAI** (verify regional availability and that it neither retains data nor uses it for training). Only approved synthetic data; nothing restricted goes to external models.
  - Deployment: Azure Container Apps or App Service. Traces in SQLite/JSONL.
- **Brief requirements applying to all options:** normal resolution path, ambiguous or unsupported case, human-handoff case, demo in **Spanish and Portuguese**, at least one learned component evaluated against a baseline, and a held-out test set with prompt-injection, expired-session, unauthorized-access, and tool-failure cases.
- **Expansion to other markets:** each option isolates country-specific details in configuration: currency, document type (CURP/CC/DNI → CPF), policies in YAML, language, and regulator. Adding Brazil, Chile, or Peru means adding a configuration file and policy documents, not writing new code.

---

## 1. Account or payment inquiries (account / payment inquiries)

**Problem:** call-center transactional volume: balances, movements, declined, pending, or reversed payments. The assistant authenticates the customer, checks balances and movements, explains the status with real data, and opens a dispute only if the customer does not recognize a charge.

- **Data:** `products` (balances, status), `transactions` (status Approved/Declined/Pending/Reversed, merchant_category, channel), `call_center_interactions` (reason_category = Transactional).
- **Learned component:** intent classifier (TF-IDF + logistic regression as baseline vs. multilingual embeddings) trained on `contact_reason` and transcripts. The split is by time, without splitting a case, and with features using only prior information (see [ML](../areas/ml.md#rigor)).
- **Deterministic controls:** the `get_transactions(customer_id)` tool validates the session; the LLM never decides amounts or statuses.
- **Handoff:** amount above a threshold or insistent customer → ticket with verified facts.
- **Why it fits the timeline:** one main table, 3–4 tools, and a short flow.
- **Expansion:** decline codes and per-country policies go in configuration; the flow is the same at any bank.

## 2. Transaction disputes (transaction-dispute intake)

**Problem:** the customer does not recognize a charge and asks to reverse it. Turning free-form conversation into a well-structured dispute (category, linked transaction, evidence) and routing it to the right queue. Today, miscategorized disputes are reopened or escalated to the regulator.

- **Data:** `complaints` (case_type = Claim, category, subcategory, reception_channel including *Regulator*, status Escalated/Rejected), `transactions`, `satisfaction_surveys`.
- **Learned component:** category and subcategory classifier, plus an escalation-risk model (probability that the case ends in *Escalated* or arrives via the regulator). The baseline is keyword rules.
- **Deterministic controls:** legal deadlines and mandatory fields per country as rules. The system does **not** resolve the dispute: it only opens, classifies, and routes it.
- **Handoff:** the package for the advisor (summary, verified facts, evidence, and open questions) is precisely the main deliverable.
- **Why it fits the timeline:** no money moves, so risk is low and the metric is clear (routing accuracy and completeness).
- **Expansion:** each country's dispute taxonomies and regulatory deadlines (SLA, service-level agreement) (Condusef and CNBV in MX, SFC in CO, BCRA in AR; Banco Central do Brasil if expanded) are mapped per country.

## 3. Card support (card-service support)

**Problem:** "I lost my card", "my card is blocked", or "why isn't it working?". A flow with concrete actions requiring explicit confirmation, ideal for showing controlled automation.

- **Data:** `products` (Credit/Debit Card, product_status Active/Blocked/Suspended), `transactions` (recent declines), `digital_events` (login or transaction errors), `call_center_interactions`.
- **Learned component:** intent classifier and "urgency or possible fraud" detector evaluated against rules.
- **Deterministic controls:** card state machine; each action (`block_card`) requires a valid session and customer confirmation, and is reported as done only if the tool confirmed it. Unblocking after fraud always goes to a human.
- **Handoff:** card replacement, fraud, or inconsistent data.
- **Why it fits the timeline:** few actions, well-defined states, and easy to test.
- **Expansion:** card logic is universal; only each market's wording and replacement policy change.

## 4. Credit-product information & simulated eligibility (credit-product info & eligibility support)

**Problem:** "Can I take out a loan or raise my limit?". The assistant explains products with policy sources, computes a **simulated** eligibility with a synthetic rules service, and explains why, without approving credit.

- **Data:** `customers`, `products` (Personal Loan, Credit Card and their balances), `transactions` (income and expenses), `marketing_campaigns`/`campaign_sends`.
- **Learned component:** risk estimation (gradient boosting) **separate** from the eligibility policy and conversation handling, as the brief requires. The baseline is simple rules.
- **Deterministic controls:** the policy service (YAML rules labeled as synthetic) produces the outcome; the LLM only communicates it. Borderline cases or those with missing data go to human review.
- **Risk:** the option with the most requirements (segment fairness, explainability, uncertainty) and the most ambitious for the timeline.
- **Expansion:** per-country policy lives in configuration and the risk model is recalibrated per market.

---

## Out of scope: app diagnostics / digital access

We evaluated it as a 5th option and **discarded** it: it is not among the original brief's examples (account/payment, card, disputes, credit), and choosing it risks the evaluation. We use `digital_events` errors only as **context** within the chosen flow (e.g., offering as a question whether the inquiry relates to a recent failure), not as a flow of its own.

---

## Comparison

Initial estimate for discussion, made before profiling the data. The measured comparison is in [flow data evidence](data-evidence.md).

| # | Option (official term) | Effort | Scope risk | Data richness | Demo |
|---|---|---|---|---|---|
| 1 | Account / payment inquiries | Low | Low | High | Good |
| 2 | Transaction disputes | Medium | Low | High | Very good |
| 3 | Card support | Low | Low | Medium | Very good |
| 4 | Credit-product info & eligibility | High | High | Medium | Good |

We decide the area split separately (see [pending decisions](../../../team/pending-decisions.md)).
