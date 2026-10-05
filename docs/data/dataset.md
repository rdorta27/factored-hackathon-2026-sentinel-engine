---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Dataset

This page is the reference for the LATAM Bank dataset. It states what exists, what each column is for and what to watch out for.

**Purpose:** understand the data in one read, without a read of the full dictionary. For the column-by-column reference (types and constraints), see [reference/latam-bank-data-dictionary.md](reference/latam-bank-data-dictionary.md).

**Related:** [data area](../build/areas/data.md) (pipeline), [ML](../build/areas/ml.md) (labels and features) and [glossary](../glossary/).

Sources: the *dataset summary* and the [data dictionary](reference/latam-bank-data-dictionary.md).

## Contents

- [The dataset](#the-dataset-official-summary) · [Tables](#tables) · [Customers and products](#dictionary-customers-and-products) · [Supporting dimensions](#dictionary-supporting-dimensions) · [Transactions](#dictionary-transactions) · [Customer contact](#dictionary-customer-contact) · [Complaints](#dictionary-complaints) · [Digital channels](#dictionary-digital-channels-and-campaigns) · [Relationships](#relationships-between-tables) · [Caveats](#general-caveats)

## The dataset (official summary)

- LATAM Bank v1.0.0 has about 19 million records in 13 tables. It is **100% synthetic**.
- Countries: Mexico, Colombia and Argentina. Period: 2023-06-17 to 2026-06-17.
- Currencies: MXN, COP, ARS and USD (daily exchange rates).
- The text is in **Spanish** only (Mexican, Colombian and Argentine accents).

### Intentional quality issues

| Issue | Rate | Implication |
|---|---|---|
| Duplicates | About 2% | Deduplication that we document and measure |
| Nulls | About 5% | They are in non-mandatory fields. The contract defines which fields can be null |
| Late arrivals | Yes | **Incremental** processing and a freshness policy. The problem statement asks for a labeled fixture only if the data is static |
| Schema evolution | Yes | Versioned contracts |

These issues are a data-engineering test. We handle them, document them and measure them. We never delete them silently.

### Measured issues (Q4-2024)

The source is the [flow measurements](../build/flows/02-flow-measurements.md).

| Issue | Measured | Implication |
|---|---|---|
| Partition and event date | About 25% of rows have an event date one day after their `process_date` partition | Define windows on event dates, never on partitions |
| Future `last_updated` in snapshots | `products` and `customers` have rows updated in 2026 and 2027 | A filter on `last_updated` drops rows. It does not rebuild a past state |
| Duplicates in complaints | 0 extra rows in Q4-2024 (the summary declares about 2%) | Keep the deduplication check. Report the gap |
| Complaint to call linkage | `origin_interaction_id` is 0% filled | Nobody can join complaints to calls or transcripts |
| Transcript text | 2 distinct 60-character prefixes over 14,023 transcripts | The text comes from templates. It has no real customer language |
| `description` and `category` | `description` contains `category` in 100% of complaints | Label leak |
| `closing_date` and `resolution_date` | 15.8% and 90.3% filled on closed complaints | The closing fields are inconsistent |
| `reason_category` | It mirrors `contact_reason` | There is no call subcategory |

## Tables

| Type | Table | Rows | Likely use |
|---|---|---|---|
| Dimension | customers | 150,000 | Customers. The basis of per-customer isolation |
| Dimension | products | 400,000 | Active financial products |
| Dimension | branches | 350 | Branches |
| Dimension | service_agents | 1,200 | Call-center agents |
| Dimension | marketing_campaigns | 200 | Campaigns |
| Facts | transactions | 5,000,000 | Movements. Charge inquiries and disputes |
| Facts | call_center_interactions | 800,000 | Contact reasons, resolution and escalation |
| Facts | call_transcripts | 200,000 | Text for intent. It covers about 25% of the interactions: check for bias |
| Facts | satisfaction_surveys | 250,000 | CSAT (Customer Satisfaction Score) and NPS (Net Promoter Score) |
| Facts | digital_events | 10,000,000 | App and web. Sample it |
| Facts | complaints | 80,000 | PQR (Peticiones, Quejas y Reclamos: requests, complaints and claims) |
| Facts | campaign_sends | 2,000,000 | Campaign sends |
| Reference | daily_exchange_rates | 3,000 | Daily exchange rates |

First, we explore the tables that link to the flow. We sample the large tables. At scale, we process only what the system needs.

## Dictionary: customers and products

| Table | Partition | Key columns | Caveat |
|---|---|---|---|
| customers | Monthly snapshot | customer_id, country, detected_accent (includes "neutral"), **segment** (Premium, Plus, Basic, Student), credit_score, estimated_monthly_income, customer_status, last_updated | Personal data (PII: document, name, email, phone, address). Never send it to the LLM |
| products | Monthly snapshot | product_id, customer_id, product_type, currency, **current_balance**, credit_limit, product_status (Active, Blocked, Closed, Suspended), days_past_due, last_transaction_date | The balance is from the latest snapshot. Compute it with later transactions or report the cut-off date |

- For ML features, use the **latest snapshot before the case date**. Never use the most recent snapshot.

## Dictionary: supporting dimensions

| Table | Partition | Key columns | Likely use |
|---|---|---|---|
| branches | Full snapshot | branch_type, address, opening_time / closing_time, has_atms, branch_status | If the flow routes to a branch: hours and status |
| service_agents | Monthly snapshot | native_accent, agent_type, experience_level, **languages**, **specialty**, avg_csat, total_monthly_interactions, agent_status | **Route the handoff** (simulated) to an agent who speaks the language of the customer and has the specialty of the flow |
| marketing_campaigns | Full snapshot | campaign_type, campaign_objective, promoted_product, target_segment, target_country, start_date / end_date | Explain demand spikes by date and country |

- `avg_csat` and `total_monthly_interactions` come from the latest month. They include the cases of that month. As features, use the snapshot of the **month before** the case.
- Advisor PII (name, email and phone): never show it to the customer or to the LLM.

## Dictionary: transactions

| Table | Partition | Key columns |
|---|---|---|
| transactions | Daily (`process_date`) | transaction_id, **transaction_date**, **process_date**, product_id, customer_id, transaction_type, amount, currency, amount_usd (can be null), channel, merchant_name, transaction_country, **transaction_status** (Approved, Declined, Pending, Reversed), **is_fraud**, **fraud_score** (0-100) |
| daily_exchange_rates | Daily | date, source_currency, target_currency, exchange_rate, buy_rate, sell_rate |

- **Two dates:** `process_date` is for the pipeline (which partitions to read, and the watermark). `transaction_date` is for the answer to the customer and for the time-based split. The difference between them measures late arrivals.
- If `amount_usd` is null, recompute it with `daily_exchange_rates` for the transaction date. Or leave it null and count it. Never invent it.
- `product_status = Blocked` is the state that a card-blocking action changes.

## Dictionary: customer contact

| Table | Partition | Key columns |
|---|---|---|
| call_center_interactions | Daily | interaction_date, customer_id, agent_id, interaction_type, channel, **contact_reason**, **reason_category** (Transactional, Product, Technical, Commercial, Complaint), duration_seconds, wait_time_seconds, **was_resolved** (FCR: first-contact resolution), **requires_followup**, detected_sentiment, **was_escalated** (to a supervisor), has_transcript |
| call_transcripts | Daily | interaction_id, full_text, **customer_text**, agent_text, detected_language, detected_accent, detected_keywords, mentioned_entities (JSON), **detected_intents**, main_topics, transcription_model, audio_quality |
| satisfaction_surveys | Daily | survey_date, interaction_id, survey_type (CSAT, NPS, CES: Customer Effort Score), main_score, nps_category, open_comments, **response_time_hours** |

- The contact reasons and their category are the basis of the analysis that justifies the flow.
- Surveys arrive after the interaction. They are outcome metrics, not features.

## Dictionary: complaints

| Table | Partition | Key columns |
|---|---|---|
| complaints | Daily | creation_date, customer_id, **case_type** (Complaint = queja, Claim = reclamo, Request = petición, Suggestion = sugerencia), category, subcategory, reception_channel (includes Regulator), affected_product_id, **origin_interaction_id**, description, claimed_amount, currency, priority, **status** (Open, In Process, Escalated, Resolved, Closed, Rejected), assignment, first-response, resolution and closure dates, **sla_breached**, resolution_days, resolution, compensation_granted, resolution_satisfaction, **is_repeat_complainer** (claims in the last 90 days) |

- **Opening fields** (the assistant completes them): case_type, category, affected_product_id, description, claimed_amount, currency, reception_channel and origin_interaction_id.
- **Lifecycle and outcome fields** (the bank defines them afterwards): status, assignment, dates, resolution, compensation and satisfaction.
- As ML features, the outcome fields are future information.
- `is_repeat_complainer`: verify whether the data owner computed it with the 90 days before each case. If you cannot confirm it, recompute it with the prior complaints.
- `origin_interaction_id` joins the complaint to the call that started it.

## Dictionary: digital channels and campaigns

| Table | Partition | Key columns |
|---|---|---|
| digital_events | Daily | event_date, customer_id (**can be null**: events before login), session_id, **event_type** (PageView, Click, FormSubmit, Login, Logout, **Error**, Purchase), event_category, channel, platform, app_version, page_url, action, product_id, **ip_address**, **ip_country**, ip_city, UTM |
| campaign_sends | Daily | send_date, campaign_id, customer_id, send_channel, send_status, was_delivered, was_opened, was_clicked, **had_conversion**, conversion_value, **send_cost** |

- **App errors:** they often come before a call or a complaint. Join them by customer and date for the demand analysis. They also give context in the conversation.
- **IP:** it is PII. It does not go to the LLM. The logs mask it. Only code uses it.
- **IP country different from the account country:** this is a risk signal, not a verdict (travel, family and VPN are possible causes). The fraud component can use it. The system can also use it to ask for extra verification in sensitive actions. Never block or discriminate by origin.
- The table has 10 million rows. Sample it for exploration.

## Assumptions

The system relies on these facts. They come from the [data dictionary](reference/) and the check against the 2024Q4 transactions. [Rationale: data assumptions](../rationale/data-assumptions.md) gives the reasons and what each fact changes.

- **Account countries are México, Colombia and Argentina only.** `customers.country` is NOT NULL with those three values. There is no Brazilian account.
- **Currency belongs to the product, not to the country.** `products.currency` takes MXN, COP, ARS or USD. A customer can hold a local product and a USD product. In 2024Q4, Colombian and Argentine charges come in their local currency and in USD. Each Mexican charge is in USD. No Mexican charge is in MXN.
- **`transaction_country` is where a purchase happened.** It is not the account country. It includes Brazil, Spain and the USA: customers of the three countries buy abroad, often in their local currency. Account statistics group by `customers.country`.
- **The canonical spelling is `México`.** The source also writes `Mexico`. Silver normalizes it (`sentinel-data-engine`, REQ-0015). In `customers` nothing needed a fix. In `transactions` the variant names purchases made in Mexico.
- **`amount_usd` is empty by design in USD charges** (it would repeat the amount). It is filled in about 95% of ARS and COP charges, from fixed synthetic exchange rates. Silver does not carry it. The rules do not need it.
- **The data is fully synthetic and in Spanish only.** The system serves Portuguese without Portuguese data (REQ-0012, REQ-0013).

## Relationships between tables

- `customer_id` links 8 tables to `customers`. It is the **mandatory filter** of each tool that reads customer data. It is always the customer of the authenticated session. The LLM never chooses it.
- Support chain: `call_center_interactions` → `call_transcripts` and `satisfaction_surveys` (by `interaction_id`) → `complaints` (by `origin_interaction_id`).
- **Null is not orphan.** A null `customer_id` in `digital_events` is valid (an event before login). A `customer_id` that does not exist in `customers` is orphaned. It goes to quarantine. The contract distinguishes the two cases.

## General caveats

- Always give an amount with its currency. Show the customer the **original** transaction currency (almost always the local currency, sometimes USD). The USD amount is for cross-country analysis.
- **Orphan records** (for example, a transaction for a nonexistent customer) are intentional. We detect them with the contract and send them to quarantine. We count them. We never return them as data of a customer.
- The data is synthetic. We apply the same access and privacy controls. We label the data as synthetic in the inventory.
- Open point, to confirm when the data arrives: whether there are several monthly snapshots, and how the data owner computed `is_repeat_complainer`.
