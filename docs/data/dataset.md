# Dataset

Reference for the LATAM Bank dataset: what exists, what each column is for, and what to watch out for.

**Purpose:** understand the data in one read, without opening the full dictionary. For the column-by-column reference (types and constraints), see [reference/latam-bank-data-dictionary.md](reference/latam-bank-data-dictionary.md). **Related:** [data area](../build/areas/data.md) (pipeline), [ML](../build/areas/ml.md) (labels and features), [glossary](../glossary/).

Sources: *dataset summary*, [data dictionary](reference/latam-bank-data-dictionary.md).

## Contents

- [The dataset](#the-dataset-official-summary) · [Tables](#tables) · [Customers and products](#dictionary-customers-and-products) · [Supporting dimensions](#dictionary-supporting-dimensions) · [Transactions](#dictionary-transactions) · [Customer contact](#dictionary-customer-contact) · [Complaints](#dictionary-complaints) · [Digital channels](#dictionary-digital-channels-and-campaigns) · [Relationships](#relationships-between-tables) · [Caveats](#general-caveats)

## The dataset (official summary)

- LATAM Bank v1.0.0: ~19 million records, 13 tables, **100% synthetic**.
- Countries: Mexico, Colombia, Argentina. Period: 2023-06-17 to 2026-06-17.
- Currencies: MXN, COP, ARS, and USD (daily exchange rates).
- Text only in **Spanish** (Mexican, Colombian, and Argentine accents).

### Intentional quality issues

| Issue | Rate | Implication |
|---|---|---|
| Duplicates | ~2% | Documented and measured deduplication |
| Nulls | ~5% | In non-mandatory fields; the contract defines which fields may be null |
| Late arrivals | Yes | **Incremental** processing and freshness policy. The problem statement asks for a labeled fixture only if the data is static |
| Schema evolution | Yes | Versioned contracts |

They are a data-engineering test: we handle, document, and measure them; we do not silently delete them.

### Measured issues (Q4-2024)

From the [flow measurements](../build/flows/02-flow-measurements.md):

| Issue | Measured | Implication |
|---|---|---|
| Partition vs event date | ~25% of rows carry an event date one day after their `process_date` partition | Windows are defined on event dates, never partitions |
| Future `last_updated` in snapshots | products and customers have rows updated in 2026 and 2027 | Filtering by `last_updated` drops rows; it does not rebuild a past state |
| Duplicates in complaints | 0 extra rows in Q4-2024 (the summary declares ~2%) | Keep the dedup check; report the gap |
| Complaint → call linkage | `origin_interaction_id` is 0% filled | Complaints cannot be joined to calls or transcripts |
| Transcript text | 2 distinct 60-character prefixes over 14,023 transcripts | Templates: no real customer language |
| `description` vs `category` | `description` contains `category` in 100% of complaints | Label leak |
| `closing_date` vs `resolution_date` | 15.8% vs 90.3% filled on closed complaints | Inconsistent closing fields |
| `reason_category` | Mirrors `contact_reason` | No call subcategory |

## Tables

| Type | Table | Rows | Likely use |
|---|---|---|---|
| Dimension | customers | 150,000 | Customers; basis for per-customer isolation |
| Dimension | products | 400,000 | Active financial products |
| Dimension | branches | 350 | Branches |
| Dimension | service_agents | 1,200 | Call-center agents |
| Dimension | marketing_campaigns | 200 | Campaigns |
| Facts | transactions | 5,000,000 | Movements; charge inquiries and disputes |
| Facts | call_center_interactions | 800,000 | Contact reasons, resolution, escalation |
| Facts | call_transcripts | 200,000 | Text for intent (covers ~25% of interactions: check for bias) |
| Facts | satisfaction_surveys | 250,000 | CSAT (Customer Satisfaction Score) and NPS (Net Promoter Score) |
| Facts | digital_events | 10,000,000 | App and web; sample it |
| Facts | complaints | 80,000 | PQR (Peticiones, Quejas y Reclamos — requests, complaints, and claims) |
| Facts | campaign_sends | 2,000,000 | Campaign sends |
| Reference | daily_exchange_rates | 3,000 | Daily exchange rates |

We first explore the tables linked to the flow and sample the large ones; at scale we process only what the system needs.

## Dictionary: customers and products

| Table | Partition | Key columns | Caveat |
|---|---|---|---|
| customers | Monthly snapshot | customer_id, country, detected_accent (includes "neutral"), **segment** (Premium, Plus, Basic, Student), credit_score, estimated_monthly_income, customer_status, last_updated | Personal data (PII: document, name, email, phone, address): never to the LLM |
| products | Monthly snapshot | product_id, customer_id, product_type, currency, **current_balance**, credit_limit, product_status (Active, Blocked, Closed, Suspended), days_past_due, last_transaction_date | The balance is from the latest snapshot: compute it with later transactions or report the cutoff date |

- For ML features, use the **latest snapshot before the case date** (never the most recent one).

## Dictionary: supporting dimensions

| Table | Partition | Key columns | Likely use |
|---|---|---|---|
| branches | Full snapshot | branch_type, address, opening_time / closing_time, has_atms, branch_status | If the flow routes to a branch: hours and status |
| service_agents | Monthly snapshot | native_accent, agent_type, experience_level, **languages**, **specialty**, avg_csat, total_monthly_interactions, agent_status | **Route the handoff** (simulated): an agent who speaks the customer's language and has the flow's specialty |
| marketing_campaigns | Full snapshot | campaign_type, campaign_objective, promoted_product, target_segment, target_country, start_date / end_date | Explain demand spikes by date and country |

- `avg_csat` and `total_monthly_interactions` are from the latest month and include that month's cases: as features, use the snapshot from the **month before** the case.
- Advisor PII (name, email, phone): never exposed to the customer or the LLM.

## Dictionary: transactions

| Table | Partition | Key columns |
|---|---|---|
| transactions | Daily (`process_date`) | transaction_id, **transaction_date**, **process_date**, product_id, customer_id, transaction_type, amount, currency, amount_usd (may be null), channel, merchant_name, transaction_country, **transaction_status** (Approved, Declined, Pending, Reversed), **is_fraud**, **fraud_score** (0-100) |
| daily_exchange_rates | Daily | date, source_currency, target_currency, exchange_rate, buy_rate, sell_rate |

- **Two dates:** `process_date` for the pipeline (which partitions to read, watermark); `transaction_date` for answering the customer and for the time-based split. The difference between them measures late arrivals.
- Null `amount_usd`: recompute with the `daily_exchange_rates` for the transaction date, or leave it null and count it; never invent it.
- `product_status = Blocked` is the state a card-blocking action would modify.

## Dictionary: customer contact

| Table | Partition | Key columns |
|---|---|---|
| call_center_interactions | Daily | interaction_date, customer_id, agent_id, interaction_type, channel, **contact_reason**, **reason_category** (Transactional, Product, Technical, Commercial, Complaint), duration_seconds, wait_time_seconds, **was_resolved** (FCR — first-contact resolution), **requires_followup**, detected_sentiment, **was_escalated** (to a supervisor), has_transcript |
| call_transcripts | Daily | interaction_id, full_text, **customer_text**, agent_text, detected_language, detected_accent, detected_keywords, mentioned_entities (JSON), **detected_intents**, main_topics, transcription_model, audio_quality |
| satisfaction_surveys | Daily | survey_date, interaction_id, survey_type (CSAT, NPS, CES — Customer Effort Score), main_score, nps_category, open_comments, **response_time_hours** |

- Contact reasons and their category: the basis of the analysis that justifies the flow.
- Surveys arrive after the interaction: they are outcome metrics, not features.

## Dictionary: complaints

| Table | Partition | Key columns |
|---|---|---|
| complaints | Daily | creation_date, customer_id, **case_type** (Complaint = queja, Claim = reclamo, Request = petición, Suggestion = sugerencia), category, subcategory, reception_channel (includes Regulator), affected_product_id, **origin_interaction_id**, description, claimed_amount, currency, priority, **status** (Open, In Process, Escalated, Resolved, Closed, Rejected), assignment, first-response, resolution, and closure dates, **sla_breached**, resolution_days, resolution, compensation_granted, resolution_satisfaction, **is_repeat_complainer** (claims in the last 90 days) |

- **Opening fields** (completed by the assistant): case_type, category, affected_product_id, description, claimed_amount, currency, reception_channel, origin_interaction_id. **Lifecycle and outcome fields** (defined by the bank afterwards): status, assignment, dates, resolution, compensation, satisfaction.
- As ML features, outcome fields are future information.
- `is_repeat_complainer`: verify whether it was computed with the 90 days before each case; if it cannot be confirmed, recompute it with prior complaints.
- `origin_interaction_id` joins the complaint to the call that originated it.

## Dictionary: digital channels and campaigns

| Table | Partition | Key columns |
|---|---|---|
| digital_events | Daily | event_date, customer_id (**may be null**: pre-login events), session_id, **event_type** (PageView, Click, FormSubmit, Login, Logout, **Error**, Purchase), event_category, channel, platform, app_version, page_url, action, product_id, **ip_address**, **ip_country**, ip_city, UTM |
| campaign_sends | Daily | send_date, campaign_id, customer_id, send_channel, send_status, was_delivered, was_opened, was_clicked, **had_conversion**, conversion_value, **send_cost** |

- **App errors:** they often precede a call or complaint. Join them by customer and date for demand analysis and to give context in the conversation.
- **IP:** PII. It does not go to the LLM, it is masked in logs, and it is used only in code.
- **IP country different from the account country:** a risk signal, not a verdict (travel, family, VPN). Useful for the fraud component or for requesting extra verification in sensitive actions; never block or discriminate by origin.
- 10-million-row table: sample it for exploration.

## Assumptions

Facts the system relies on, taken from the [data dictionary](reference/) and checked against the 2024Q4 transactions. The reasons and what they change are in [rationale: data assumptions](../rationale/data-assumptions.md).

- **Account countries are México, Colombia and Argentina only.** `customers.country` is NOT NULL with those three values. There is no Brazilian account.
- **Currency belongs to the product, not the country.** `products.currency` takes MXN, COP, ARS or USD, so a customer may hold a local and a USD product. In 2024Q4, Colombian and Argentine charges come in their local currency and in USD; every Mexican charge is in USD and none in MXN.
- **`transaction_country` is where a purchase happened**, not the account country. It includes Brazil, Spain and the USA: customers of the three countries buying abroad, often in their local currency. Account statistics group by `customers.country`.
- **Canonical spelling is `México`.** The source also writes `Mexico`; Silver normalizes it (`sentinel-data-engine`, REQ-0015). In `customers` there was nothing to fix; in `transactions` the variant names purchases made in Mexico.
- **`amount_usd` is empty by design in USD charges** (it would repeat the amount) and filled in about 95% of ARS and COP charges, from fixed synthetic exchange rates. Silver does not carry it; the rules do not need it.
- **The data is fully synthetic and Spanish only.** Portuguese is served without Portuguese data (REQ-0012, REQ-0013).

## Relationships between tables

- `customer_id` links 8 tables to `customers`. It is the **mandatory filter** of every tool that reads customer data: always the authenticated session's customer, never chosen by the LLM.
- Support chain: `call_center_interactions` → `call_transcripts` and `satisfaction_surveys` (by `interaction_id`) → `complaints` (by `origin_interaction_id`).
- **Null is not orphan:** a null `customer_id` in `digital_events` is valid (pre-login event); a `customer_id` that does not exist in `customers` is orphaned and goes to quarantine. The contract distinguishes them.

## General caveats

- Amounts always with their currency. The customer is shown the **original** transaction currency (almost always the local one; it may be USD). The USD amount is for cross-country analysis.
- **Orphan records** (e.g., a transaction for a nonexistent customer): intentional. We detect them with the contract, send them to quarantine, count them, and never return them as a customer's data.
- Even though the data is synthetic, we apply access and privacy controls equally, and we label it as synthetic in the inventory.
- Pending confirmation once the data arrives: whether there are multiple monthly snapshots and how `is_repeat_complainer` was computed.
