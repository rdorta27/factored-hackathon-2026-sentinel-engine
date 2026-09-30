# Requirements

What the system must do to meet the hackathon brief. Each requirement has an ID (`REQ-####`) that the rest of the documentation cites, and this table doubles as the traceability matrix: every requirement is tied to the official document it comes from, the evaluation criterion it serves, the area that owns it, the evidence that will prove it, and its status.

**Purpose:** prioritize the work and spot evaluation criteria that still lack evidence. **Related:** [The Challenge](../understand/overview.md), [dataset](../understand/dataset.md), [glossary](../understand/glossary/).

## Hackathon material

Requirements come from four official documents, plus clarifications published in the help channel. They are not in the repository; each teammate keeps a copy, and we cite them by section or page.

| Document | Cited as | What it defines | Requirements that cite it |
|---|---|---|---|
| Problem statement (*Factored AI & Data Hackathon 2026*) | Problem statement: *section* | Scope, what the solution must demonstrate, data and execution boundaries, submission | 38 |
| Kickoff deck (*Datathon 2026 kickoff*) | Kickoff p. *N* | Evaluation criteria, workflows, multilingual support, headline metrics | 36 |
| Dataset summary (*LATAM Bank*) | Dataset summary | Tables, volumes and the intentional quality problems (duplicates, nulls, late arrivals, schema changes) | 6 |
| Data dictionary (*LATAM Bank*) | Dictionary | Columns, partitions and relationships between tables | 1 |
| Answers in the hackathon help channel | Help channel (*date*) | Clarifications: what counts as a learned component, cloud deployment, sizing, external data, deadline | 6 |

A requirement with no official source is marked **Own**: a team design decision, linked to where it is explained (10 requirements rely only on it; others combine it with an official source). The dataset documents shape the data requirements through [dataset](../understand/dataset.md) and are cited where a row depends on a declared property of the data.

## Classification

| Column | Values |
|---|---|
| **Type** | **F** = functional (what it does) · **NF** = non-functional (how: security, reliability, operations) · **DML** = data and ML · **E** = delivery |
| **Priority** | **P0** = mandatory: code, results and README ready by Fri 10/2; the presentation and the video are finished by Mon 10/5 · **P1** = scores points, from Thu 10/1 if P0 is on track · **P2** = only if time remains. Code freezes on Fri 10/2 at night |
| **Flow** | "All", or the flow it depends on (transaction disputes, see [decision 003](../build/decisions/003-disputes-flow.md)) |
| **Criterion** | Kickoff evaluation criterion: Rationale, AI Engineering, Data Engineering, Data Analytics, Machine Learning |
| **Area** | Areas that work on it; the first one owns it and the rest collaborate: [ai](../build/areas/ai.md) · [ml](../build/areas/ml.md) · [data](../build/areas/data.md) · [analysis](../build/areas/analysis.md) |
| **Status** | Pending, In progress, Done. Updated when the task that covers it closes |
| **Source** | Official document and section or page (see [hackathon material](#hackathon-material)), or **Own** |

## Summary by priority

| Priority | Count | What it includes |
|---|---|---|
| P0 | 41 | The 3 demo cases, es-419 and pt-BR, verification, permissions in code, handoff, learned component vs baseline, outcome metrics, explicit trade-offs, pipeline with contracts and real incremental processing, failure tests, deliverables, delivery language, path to production, sizing |
| P1 | 12 | Tracking, business outcomes and ROI, observability, retries, breakdown by language and country, fine-grained conversation rules |
| P2 | 4 | Country as configuration, app-error context, handoff routing, LLM judge |

## Status by priority

Counted from the *Status* column of the tables below; update it whenever a status changes.

| Priority | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| P0 | 41 | 3 | 9 | 29 | 7% |
| P1 | 12 | 0 | 3 | 9 | 0% |
| P2 | 4 | 0 | 1 | 3 | 0% |
| **Total** | **57** | 3 | 13 | 41 | 5% |

## Functional (F)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0001 | Keep conversation context | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Demo | Pending |
| REQ-0002 | Clarify ambiguous requests or abstain from unsupported ones | P0 | All | AI Engineering | ai | Problem statement: Scope; What your solution should demonstrate 2 · Kickoff p. 11 | Ambiguous-case demo | Pending |
| REQ-0003 | Answer only with verified records; if the data does not exist, say so | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 13 | Demo + logs | Pending |
| REQ-0004 | Use tools safely to execute the flow; no real movement of money or live decisions (simulated actions only) | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2; Data and execution boundaries · Kickoff p. 11 | Tool contracts | In progress |
| REQ-0006 | Define what it answers alone, what requires confirmation, and when to escalate | P0 | All | Rationale | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11 | [Conversation](../build/conversation.md) | In progress |
| REQ-0008 | Structured JSON handoff: request, verified facts, actions, evidence, open questions; no raw transcript | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14 | Schema + example | In progress |
| REQ-0009 | Demo: normal case resolved per policies | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0010 | Demo: ambiguous or unsupported case (clarifies or abstains) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0011 | Demo: case requiring a human (escalates with handoff) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0012 | Robust interactions in Spanish and Portuguese; the dataset is Spanish-only, so pt-BR cases are team-generated and labeled as such | P0 | All | AI Engineering / ML | ai, ml | Problem statement: Scope · Kickoff p. 10 · Dataset summary | pt-BR demo + metrics by language | Pending |
| REQ-0033 | Policy decides, the LLM converses: it neither approves nor invents rules. The source's risk/eligibility separation is credit-specific and does not apply to disputes | P0 | All | AI Engineering / ML | ai, ml | Problem statement: Data and execution boundaries; What your solution should demonstrate 3 | Architecture | Done |
| REQ-0038 | Simple frontend for using the system (e.g., chat); dashboard not required (scope decision: no dashboard) | P0 | All | AI Engineering | ai | Kickoff p. 20 | Demo | Pending |
| REQ-0039 | Declare data freshness ("updated through…"); never claim anything more recent | P0 | All | AI Engineering / Data Engineering | ai, data | Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) · Dataset summary (data ends 2026-06-17) | Demo + tools with "updated through" | Pending |
| REQ-0040 | Request to speak to a person: a single offer to help and, if they insist, escalate immediately | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person) | Human-case demo | Pending |
| REQ-0041 | Show amounts in the transaction's original currency; language follows the customer, currency follows the account | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) · Dataset summary (local currency and USD) | pt-BR demo | Pending |
| REQ-0042 | Open disputes with minimum effort: show candidate transactions instead of asking for amounts | P1 | Disputes | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-dispute) | Demo | Pending |
| REQ-0043 | Check the charge status (Pending, Reversed) before opening a dispute | P1 | Disputes, accounts | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-dispute) | Demo | Pending |
| REQ-0044 | Neutral Spanish, with local acronyms and terms explained; understand terms from other countries | P1 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) | Demo | Pending |
| REQ-0045 | Offer recent app-error context as a question (auxiliary context, not its own flow) | P2 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#app-context) | Demo | Pending |
| REQ-0046 | Route the handoff to an advisor with the right language and specialty (simulated) | P2 | All | AI Engineering | ai | Own: [AI](../build/areas/ai.md#simulated-routing) | Handoff example | Pending |

## Non-functional (NF)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0005 | Report only verified actions (timeout is not success) | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Tool-failure test | Pending |
| REQ-0007 | Permissions and policies in code, in addition to the prompt | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13 | Code + adversarial test | Pending |
| REQ-0021 | Failure tests: bad or missing data, expired session, unauthorized access, prompt injection, tool failure, multilingual ambiguity | P0 | All | Machine Learning | ml, ai | Problem statement: What your solution should demonstrate 5 · Kickoff p. 13 | Adversarial-set results | Pending |
| REQ-0027 | Authentication with test session, per-customer access control, retention policy | P0 | All | AI Engineering / Data Engineering | ai, data | Problem statement: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15 | Test session + policy | Pending |
| REQ-0028 | Reproducibility: setup, versioning, repeatable evaluation | P0 | All | Rationale | all | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Setup README | Pending |
| REQ-0047 | The LLM receives no identifiers or personal data (PII), and no restricted data goes in external model requests; tools filter by the session customer | P0 | All | AI Engineering | ai | Problem statement: Data and execution boundaries · Own: [security](../build/security.md#llm-visibility) | Code + adversarial test | Pending |
| REQ-0048 | Decision order: policy in code > learned component > LLM | P0 | All | Rationale / ML | ai, ml | Problem statement: introduction · Kickoff p. 11 · Own: [system](../architecture/specification.md#decision-priority) | [Decision priority](../architecture/specification.md#decision-priority) | Done |
| REQ-0056 | Explicit trade-offs across autonomy, accuracy, latency, cost, and human oversight; justify where AI is used and where deterministic logic is preferable | P0 | All | Rationale | all | Problem statement: introduction · Kickoff p. 11 | Decisions + presentation | In progress |
| REQ-0025 | Observability: execution traces and logs, with country and language | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Traces and logs | In progress |
| REQ-0026 | Bounded retries, safe fallback; idempotent actions | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Tool-failure test | Pending |
| REQ-0029 | Explanations based on sources, rules, and logs; not on model reasoning | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 | Audit logs | In progress |
| REQ-0032 | Mock tools with documented contracts and limitations | P1 | All | AI Engineering | ai | Problem statement: Data and execution boundaries | Tool contracts | In progress |
| REQ-0049 | Country is configuration, not code | P2 | All | Rationale | ai | Own: [AI](../build/areas/ai.md#technical-rules) | Configuration file | In progress |

## Data and ML (DML)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0014 | Data-backed problem, with reproducible analysis justifying the flow | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 1 · Kickoff p. 13 | Reproducible analysis | Done |
| REQ-0015 | Repeatable pipeline with strict contracts, quality, lineage, and freshness; handles the declared ~2% duplicates, ~5% nulls and orphaned records | P0 | All | Data Engineering | data | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Dataset summary · Dictionary | Pipeline + quality report | In progress |
| REQ-0016 | At least one learned component compared against a baseline on held-out; a prompted or fine-tuned LLM counts if defined, evaluated and justified | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Help channel (9/28) | Results table | Pending |
| REQ-0017 | Valid labels with no data leakage; justify metrics, thresholds, and splits | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 | Split description | In progress |
| REQ-0020 | Baseline and system on the same held-out, with realistic distribution | P0 | All | Machine Learning | ml | Problem statement: Evaluation evidence · Kickoff p. 12 | Set descriptions | Pending |
| REQ-0022 | Metrics with n, case mix, versions, and variability; include failures | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 5; Evaluation evidence | Metrics report | Pending |
| REQ-0055 | Report the mandatory outcome metrics: safe automated resolution (plus share attempted), containment, escalation quality (missed and unnecessary transfers), unsafe outcomes with counts and denominators, p50/p95 latency, cost per attempted case and per successful resolution ("not defined" if none) | P0 | All | Data Analytics | analysis, ml | Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12 | [Metrics](../build/metrics.md) report | Pending |
| REQ-0053 | Sizing and its limits: disputes per day in the data, capacity the prototype is designed for, and what changes at real volume | P0 | All | Data Analytics | analysis | Help channel (9/28) | Sizing section | In progress |
| REQ-0057 | Intended customer and business outcomes, with cost-per-resolution ROI against the baseline; projected savings labeled as projections | P1 | All | Data Analytics | analysis | Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13 | ROI section | Pending |
| REQ-0031 | Only approved data under the published data-use terms; label each source (real, de-identified, synthetic, team-generated) | P0 | All | Data Engineering | data | Problem statement: Data and execution boundaries | Source inventory | Pending |
| REQ-0054 | External data only if justified: source, license, why it is needed, no PII, labeled as external | P1 | All | Data Engineering | data, ml | Help channel (9/28) | Source inventory | Pending |
| REQ-0018 | Real incremental processing of the declared late arrivals, duplicates and schema evolution; a labeled test fixture proves update correctness | P0 | All | Data Engineering | data | Problem statement: Architecture freedom · Dataset summary | Update fixture | Pending |
| REQ-0019 | Experiment tracking: model and prompt versions, parameters, metrics | P1 | All | Machine Learning | ml | Kickoff p. 20 | Experiment log | Pending |
| REQ-0024 | Breakdown by language, country, and authorized segment, investigating disparities (fairness) and stating small-sample limits; separate offline, simulation, and projection | P1 | All | Data Analytics | analysis | Problem statement: Evaluation evidence | Metrics report | Pending |
| REQ-0050 | Monitoring by country (latency, failures, escalations, complaints) | P1 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring) | Report by country | Pending |
| REQ-0023 | If there is an LLM judge: documented rubric validated on a sample against human or deterministic judgments | P2 | If applicable | Machine Learning | ml | Problem statement: Evaluation evidence | Rubric + validated sample | Pending |

## Delivery (E)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0034 | Public repository `factored-hackathon-2026-[team]`, without secrets or restricted data; all links sent to `hackathon.admin@factored.ai` | P0 | All | Rationale | all | Kickoff p. 18 | Repo link | Pending |
| REQ-0035 | Link to the deployed tool, with usage and spending limits; a minimal deployment is enough, cloud is not mandatory | P0 | All | AI Engineering | ai | Kickoff p. 18 · Help channel (9/28) | Link | Pending |
| REQ-0036 | 4-to-6-slide presentation | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#presentation) | Pending |
| REQ-0037 | Short, mandatory video pitch: working demo and core architecture decisions | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#video-pitch) | Pending |
| REQ-0051 | Repo README, presentation (4 to 6 slides), video script, AND `docs/` and `team/` all in English | P0 | All | Rationale | all | Own: [language](../build/delivery.md#language) | [Pre-submission check](../build/delivery.md#language) | Pending |
| REQ-0013 | Report data and language-coverage limitations, including that the dataset has no Portuguese text and covers only MX, CO and AR | P0 | All | Rationale | analysis | Problem statement: Scope · Kickoff p. 15 · Dataset summary | Limitations section | Pending |
| REQ-0030 | Declare what is missing: capacity, data, languages, deployment, risks | P0 | All | Rationale | all | Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 · Help channel (9/28) | Limitations section | In progress |
| REQ-0052 | Credible path to production: how it deploys, scales, is monitored and secured, and what changes from the prototype | P0 | All | AI Engineering / Rationale | ai, all | Help channel (9/28) · Kickoff p. 15 | [Path to production](../architecture/specification.md#path-to-production) | In progress |

## Future work (not requirements)

- Expansion to other Latin American countries. The design makes it easier with REQ-0049 (country as configuration); it would require data, rules, currency, and tests for each new country.
- Streaming: only if a flow needs seconds-level freshness.

## Open questions

- How do we build the reference labels for evaluation (which cases require a human)?
