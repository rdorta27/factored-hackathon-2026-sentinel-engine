---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Glossary — en-US (canonical)

These terms are shared by each locale. A local term keeps its original spelling. It has an English explanation on first use.

Use one term for one concept. The agreed terms are *handoff*, *cut-off*, *held-out*, *baseline*, *simulation* and *mock*. Do not use a synonym for them.

## Business acronyms and terms

The hackathon audience is technical (software and data). Always explain these contact-center and banking terms.

| Term | English | Meaning |
|---|---|---|
| CSAT | Customer Satisfaction Score | The satisfaction with one interaction, from 1 to 5 |
| NPS | Net Promoter Score | The question is "Would you recommend the bank?" The scale is 0 to 10. The score is the % of 9-10 minus the % of 0-6 (from −100 to +100) |
| CES | Customer Effort Score | How easy it was to resolve the issue |
| FCR | First Call Resolution | The contact is resolved at first contact. No callback is necessary |
| IVR | Interactive Voice Response | An automated phone menu ("press 1 for…") |
| STT | Speech-to-Text | The conversion of audio to text |
| PQR | — | *Peticiones, quejas y reclamos* (CO): the system where customers file cases |
| Chargeback | Chargeback | The reversal of an unrecognized or incorrect card charge |
| Pre-authorization | Pre-authorization | A temporary hold. It shows as pending and usually releases itself |
| MCC | Merchant Category Code | The code of the merchant type |
| CLV | Customer Lifetime Value | The revenue from a customer over the whole relationship |
| Churn | Churn | The loss of customers |
| Days past due | Days past due | The delay of a loan payment, in days |
| SLA | Service Level Agreement | A committed deadline (for example, answer a dispute in 15 days). A missed deadline is "SLA breached" |
| UTM | Urchin Tracking Module | The parameters of a campaign link. They show the campaign and the channel of a visit |
| Conversion | Conversion | The customer did what the campaign wanted (for example, requested the card) |
| Supervisor | Supervisor | The lead of a group of advisors. The supervisor receives the cases that an advisor cannot resolve |

## Architecture

| Build | Functional | Official | Definition |
|---|---|---|---|
| Service layer | Real-time support | — | Conversation, orchestrator, tools and actions. It answers the customer at once |
| Data layer | Data processing | Pipeline | It prepares the data that the service layer reads: contracts, deduplication, upsert and stores |
| Orchestrator | Assistant | Agent | The component that understands, decides, acts, verifies and makes a handoff. In this repository, "agent" means only this AI component. The human who takes a handoff is the **advisor** |
| Advisor | Advisor | Agent (call center) | The human who receives the handoff. *Asesor* in Spanish, *atendente* in Portuguese |
| Tool | Query or operation | Tool | A function that the orchestrator calls to read data or run actions, with access control |
| Gold | (Simulated) banking core | — | The transactions of each customer that the tools read, with their cut-off date. The pipeline fills it |
| Disputes store | Dispute registry | — | The record that the tools write and read back before they report a case number. It is not Gold. The demo keeps it in SQLite. Postgres is the production backend of the same contract |
| Analytical store | — | — | Data for analysis, baseline and training |
| Mask / unmask | — | — | **Mask:** replace a personal value (document or card number) with a token before it reaches the LLM or the logs. **Unmask:** code swaps the token back for the real value. It does this only inside a tool, and it never uses the value as a lookup key. See [decision 004](../build/decisions/004-pii-lifecycle.md) |
| Token vault | — | — | An encrypted map from tokens to masked values, for each session. The system discards it when the session ends |

## Support

| Build | Functional | Official | Definition |
|---|---|---|---|
| Handoff | Escalation to an advisor | Handoff / escalation | The system passes the case to a person with a structured summary |
| Containment | Cases without escalation | Containment | Cases that end without a person. It is not the same as resolved |
| Safe automated resolution | Resolution without an advisor | Safe automated resolution | A case that the system resolves correctly and within policy, with no human |
| Abstention | Unserved request | Abstention | The system decides not to act and explains why |

## Use cases

| Build | Functional | Official | Definition |
|---|---|---|---|
| Flow selection | — | Task selection | The choice of the support job that the assistant performs. The project (the assistant) is fixed |
| Transaction-disputes flow | Unrecognized-charge dispute / chargeback | Transaction disputes / transaction-dispute intake | The customer does not recognize a charge and asks for a reversal |
| — | Complaint | Complaint | Dissatisfaction with the service. In the dataset, it is part of PQR |
| — | PQR | Complaints (PQR) | Requests, complaints and claims |
| Card flow | Card services | Card support | Block, replace and card questions |
| Account and payment flow | Account and payment inquiries | Account / payment inquiries | Balances, transactions and payment status |
| Credit flow | Credit-product info and eligibility | Credit-product info & eligibility | Product terms and a simulated eligibility outcome |

## Data

| Build | Functional | Official | Definition |
|---|---|---|---|
| Upsert | Insert or update | — | If the key exists, update the row. If not, insert it. It is idempotent |
| Watermark | Progress mark | — | The last partition that the pipeline processed |
| Reprocessing window | — | — | The last N days that the pipeline processes again to catch late arrivals |
| Data contract | — | Data contract | The schema and the rules that data must meet to enter |
| Freshness | Updated through | Freshness | The lag between an event and the moment that the system sees it |
| Idempotent | — | — | A repeated operation gives the same result |
| Orphan record | — | Orphaned record | A record that points to a record that does not exist (for example, a transaction of a nonexistent customer) |

## Evaluation

| Build | Functional | Official | Definition |
|---|---|---|---|
| Held-out | Reserved test cases | Held-out | Cases that nobody uses to tune the system. The team measures them once, at the end |
| Baseline | Comparison point | Baseline | A simple version that the team compares the system against |
| Cut-off | Confidence threshold | — | A threshold on the confidence of the router. `t_act` is the lowest confidence at which the system acts on a label. `t_abstain` is the confidence below which the system asks the customer to clarify. See [decision 018](../build/decisions/018-evaluation-acceptance.md) |
| Simulation | Test on team-written cases | — | A measurement on cases that the team generated. It is not a measurement on production traffic. See [what is real](../architecture/what-is-real.md) |
| Mock | Stand-in component | — | A stand-in with the same contract as the production component. Production replaces the backend, not the code. See [what is real](../architecture/what-is-real.md) |
| Data leakage | — | Leakage | Test information that leaks into training and inflates the metrics. Causes: a split by case, a split that sees the future, or a feature that uses later information |
| Adversarial set | Attack tests | — | Injection, unauthorized-access and failure cases |
| p50 / p95 | Typical time / slow-case time | p50 / p95 latency | Latency percentiles |
