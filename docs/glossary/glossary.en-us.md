# Glossary — en-US (canonical)

Shared terms for every locale. Local terms keep their original spelling with an English explanation on first use.

## Business acronyms and terms

The hackathon audience is technical (software, data). These contact-center and banking terms are always explained.

| Term | English | Meaning |
|---|---|---|
| CSAT | Customer Satisfaction Score | Satisfaction with a single interaction, 1 to 5 |
| NPS | Net Promoter Score | "Would you recommend the bank?" 0 to 10; % of 9-10 minus % of 0-6 (from −100 to +100) |
| CES | Customer Effort Score | How easy it was to resolve the issue |
| FCR | First Call Resolution | Resolved on first contact, no callback needed |
| IVR | Interactive Voice Response | Automated phone menu ("press 1 for…") |
| STT | Speech-to-Text | Audio-to-text conversion |
| PQR | — | *Peticiones, quejas y reclamos* (CO): system where cases are filed |
| Chargeback | Chargeback | Reversal of an unrecognized or incorrect card charge |
| Pre-authorization | Pre-authorization | Temporary hold; shows as pending and usually releases itself |
| MCC | Merchant Category Code | Merchant-type code |
| CLV | Customer Lifetime Value | Revenue from a customer over the whole relationship |
| Churn | Churn | Customer attrition |
| Days past due | Days past due | Loan-payment delay in days |
| SLA | Service Level Agreement | Committed deadline (e.g. answer a dispute in 15 days); missing it is "SLA breached" |
| UTM | Urchin Tracking Module | Campaign-link parameters showing which campaign and channel a visit came from |
| Conversion | Conversion | The customer did what the campaign wanted (e.g. requested the card) |
| Supervisor | Supervisor | Lead of a group of advisors; receives cases an advisor cannot resolve |

## Architecture

| Build | Functional | Official | Definition |
|---|---|---|---|
| Service layer | Real-time support | — | Conversation, orchestrator, tools and actions. Answers the customer instantly |
| Data layer | Data processing | Pipeline | Prepares the data the service layer reads: contracts, deduplication, upsert, stores |
| Orchestrator | Assistant | Agent | Component that understands, decides, acts, verifies and escalates. In this repo, "agent" only means this AI component; the human who takes a handoff is the **advisor** |
| Advisor | Advisor | Agent (call center) | Human who receives the handoff; *asesor* in Spanish, *atendente* in Portuguese |
| Tool | Query or operation | Tool | Function the orchestrator calls to read data or run actions, with access control |
| Gold | (Simulated) banking core | — | Per-customer transactions the tools read, with their cutoff date; filled by the pipeline |
| Disputes store | Dispute registry | — | Record the tools write and read back before reporting a case number. Not Gold. The demo keeps it in memory; SQLite and Postgres are the production backend of the same contract |
| Analytical store | — | — | Data for analysis, baseline and training |
| Mask / unmask | — | — | **Mask:** replace a personal value (document, card number) with a token before it reaches the LLM or the logs. **Unmask:** code swaps the token back for the real value, only inside a tool, and never uses it as a lookup key. See [decision 004](../build/decisions/004-pii-lifecycle.md) |
| Token vault | — | — | Per-session, encrypted map from tokens to the masked values; discarded when the session ends |

## Support

| Build | Functional | Official | Definition |
|---|---|---|---|
| Handoff | Escalation to an advisor | Handoff / escalation | Passing the case to a person with a structured summary |
| Containment | Cases without escalation | Containment | Cases ending without a person; not the same as resolved |
| Safe automated resolution | Resolution without an advisor | Safe automated resolution | Case resolved correctly and within policy, with no human |
| Abstention | Unserved request | Abstention | The system decides not to act and explains why |

## Use cases

| Build | Functional | Official | Definition |
|---|---|---|---|
| Flow selection | — | Task selection | Which support job the assistant performs; the project (the assistant) is fixed |
| Transaction-disputes flow | Unrecognized-charge dispute / chargeback | Transaction disputes / transaction-dispute intake | The customer does not recognize a charge and asks to reverse it |
| — | Complaint | Complaint | Dissatisfaction with the service; in the dataset, part of PQR |
| — | PQR | Complaints (PQR) | Requests, complaints and claims |
| Card flow | Card services | Card support | Block, replace, card questions |
| Account and payment flow | Account and payment inquiries | Account / payment inquiries | Balances, transactions, payment status |
| Credit flow | Credit-product info and eligibility | Credit-product info & eligibility | Product terms and simulated eligibility outcome |

## Data

| Build | Functional | Official | Definition |
|---|---|---|---|
| Upsert | Insert or update | — | If the key exists, update; else insert. Idempotent |
| Watermark | Progress mark | — | Up to which partition was processed |
| Reprocessing window | — | — | Last N days reprocessed to catch late arrivals |
| Data contract | — | Data contract | Schema and rules data must meet to enter |
| Freshness | Updated through | Freshness | Lag between something happening and the system seeing it |
| Idempotent | — | — | Repeating the operation gives the same result |
| Orphan record | — | Orphaned record | Record pointing to one that does not exist (e.g. a transaction of a nonexistent customer) |

## Evaluation

| Build | Functional | Official | Definition |
|---|---|---|---|
| Held-out | Reserved test cases | Held-out | Cases never used to tune the system; measured once at the end |
| Baseline | Comparison point | Baseline | Simple version the system is compared against |
| Data leakage | — | Leakage | Test information leaking into training and inflating metrics: split by case, splits seeing the future, or features using later information |
| Adversarial set | Attack tests | — | Injection, unauthorized-access, failure cases |
| p50 / p95 | Typical time / slow-case time | p50 / p95 latency | Latency percentiles |
