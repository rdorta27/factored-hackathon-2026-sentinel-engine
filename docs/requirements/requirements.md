# Requirements

What the system must satisfy. Each requirement has an ID `REQ-####` that we use in the rest of the documentation. This table is also the traceability matrix: each requirement with its evaluation criterion, area, evidence, and status.

**Purpose:** prioritize the work and see which criterion still lacks evidence. **Related:** [challenge summary](../understand/overview.md), [glossary](../understand/glossary/).

## Classification

| Column | Values |
|---|---|
| **Type** | **F** = functional (what it does) · **NF** = non-functional (how: security, reliability, operations) · **DML** = data and ML · **E** = delivery |
| **Priority** | **P0** = mandatory, ready by Fri 10/2 · **P1** = scores points, starting Thu 10/1 if P0 is on track · **P2** = if time remains. Code freezes Fri 10/2 at night |
| **Flow** | "All", or the flow it depends on (proposal: transaction disputes, see [decision 003](../build/decisions/003-disputes-flow.md)) |
| **Criterion** | Kickoff evaluation criterion: Rationale, AI Engineering, Data Engineering, Data Analytics, Machine Learning |
| **Area** | Areas working on the requirement; the first one owns it and the others collaborate: [ai](../build/areas/ai.md) · [ml](../build/areas/ml.md) · [data](../build/areas/data.md) · [analysis](../build/areas/analysis.md) |
| **Status** | Pending, In progress, Done. We update it when closing each task |
| **Source** | Official document and section (problem statement) or page (kickoff), or **Own** = team design decision, with a link to where it is explained |

The official documents (problem statement, kickoff, dataset summary, and dictionary) are not in the repository: we cite them by section or page.

## Summary by priority

| Priority | Count | What it includes |
|---|---|---|
| P0 | 36 | The 3 demo cases, ES and PT, verification, permissions in code, handoff, learned component vs baseline, pipeline with contracts, failure tests, deliverables, delivery language |
| P1 | 11 | Tracking, real incremental processing, observability, retries, breakdown by language and country, fine-grained conversation rules |
| P2 | 4 | Country as configuration, app-error context, handoff routing, LLM judge |

## Functional (F)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0001 | Keep conversation context | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Demo | Pending |
| REQ-0002 | Clarify ambiguous requests or abstain from unsupported ones | P0 | All | AI Engineering | ai | Problem statement: Scope; What your solution should demonstrate 2 · Kickoff p. 11 | Ambiguous-case demo | Pending |
| REQ-0003 | Answer only with verified records; if the data does not exist, say so | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 13 | Demo + logs | Pending |
| REQ-0004 | Use tools safely to execute the flow | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Tool contracts | Pending |
| REQ-0006 | Define what it answers alone, what requires confirmation, and when to escalate | P0 | All | Rationale | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11 | [Conversation](../build/conversation.md) | Pending |
| REQ-0008 | Structured JSON handoff: request, verified facts, actions, evidence, open questions; no raw transcript | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14 | Schema + example | Pending |
| REQ-0009 | Demo: normal case resolved per policies | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0010 | Demo: ambiguous or unsupported case (clarifies or abstains) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0011 | Demo: case requiring a human (escalates with handoff) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Demo + video | Pending |
| REQ-0012 | Robust interactions in Spanish and Portuguese | P0 | All | AI Engineering / ML | ai, ml | Problem statement: Scope · Kickoff p. 10 | PT demo + metrics by language | Pending |
| REQ-0033 | Separate conversation, risk, and eligibility policy; the LLM neither approves nor invents rules | P0 | Credit | AI Engineering / ML | ai, ml | Problem statement: Data and execution boundaries | Architecture | Pending |
| REQ-0038 | Simple frontend for using the system (e.g., chat); dashboard not required (scope decision: no dashboard) | P0 | All | AI Engineering | ai | Kickoff p. 20 | Demo | Pending |
| REQ-0039 | Declare data freshness ("updated through…"); never claim anything more recent | P0 | All | AI Engineering / Data Engineering | ai, data | Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) | Demo + tools with "updated through" | Pending |
| REQ-0040 | Request to speak to a person: a single offer to help and, if they insist, escalate immediately | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person) | Human-case demo | Pending |
| REQ-0041 | Show amounts in the transaction's original currency; language follows the customer, currency follows the account | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) | PT demo | Pending |
| REQ-0042 | Open claims with minimum effort: show candidate transactions instead of asking for amounts | P1 | Claims | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-claim) | Demo | Pending |
| REQ-0043 | Check the charge status (Pending, Reversed) before opening a claim | P1 | Claims, accounts | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-claim) | Demo | Pending |
| REQ-0044 | Neutral Spanish, with local acronyms and terms explained; understand terms from other countries | P1 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) | Demo | Pending |
| REQ-0045 | Offer recent app-error context as a question (auxiliary context, not its own flow) | P2 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#app-context) | Demo | Pending |
| REQ-0046 | Route the handoff to an agent with the right language and specialty (simulated) | P2 | All | AI Engineering | ai | Own: [AI](../build/areas/ai.md#simulated-routing) | Handoff example | Pending |

## Non-functional (NF)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0005 | Report only verified actions (timeout is not success) | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Tool-failure test | Pending |
| REQ-0007 | Permissions and policies in code, in addition to the prompt | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13 | Code + adversarial test | Pending |
| REQ-0021 | Failure tests: bad or missing data, expired session, unauthorized access, prompt injection, tool failure, multilingual ambiguity | P0 | All | Machine Learning | ml, ai | Problem statement: What your solution should demonstrate 5 · Kickoff p. 13 | Adversarial-set results | Pending |
| REQ-0027 | Authentication with test session, per-customer access control, retention policy | P0 | All | AI Engineering / Data Engineering | ai, data | Problem statement: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15 | Test session + policy | Pending |
| REQ-0028 | Reproducibility: setup, versioning, repeatable evaluation | P0 | All | Rationale | all | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Setup README | Pending |
| REQ-0047 | The LLM receives no identifiers or personal data; tools filter by the session customer | P0 | All | AI Engineering | ai | Own: [security](../build/security.md#llm-visibility) | Code + adversarial test | Pending |
| REQ-0048 | Decision order: policy in code > predictor > LLM | P0 | All | Rationale / ML | ai, ml | Own: [architecture](../understand/architecture.md#decision-priority) | [Architecture](../understand/architecture.md) | Pending |
| REQ-0025 | Observability: execution traces and logs, with country and language | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Traces and logs | Pending |
| REQ-0026 | Bounded retries, safe fallback; idempotent actions | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Tool-failure test | Pending |
| REQ-0029 | Explanations based on sources, rules, and logs; not on model reasoning | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 | Audit logs | Pending |
| REQ-0032 | Mock tools with documented contracts and limitations | P1 | All | AI Engineering | ai | Problem statement: Data and execution boundaries | Tool contracts | Pending |
| REQ-0049 | Country is configuration, not code | P2 | All | Rationale | ai | Own: [AI](../build/areas/ai.md#technical-rules) | Configuration file | Pending |

## Data and ML (DML)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0014 | Data-backed problem, with reproducible analysis justifying the flow | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 1 · Kickoff p. 13 | Reproducible analysis | Pending |
| REQ-0015 | Repeatable pipeline with strict contracts, quality, lineage, and freshness | P0 | All | Data Engineering | data | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 | Pipeline + quality report | Pending |
| REQ-0016 | At least one learned component compared against a baseline on held-out | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 | Results table | Pending |
| REQ-0017 | Valid labels with no data leakage; justify metrics, thresholds, and splits | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 | Split description | Pending |
| REQ-0020 | Baseline and system on the same held-out, with realistic distribution | P0 | All | Machine Learning | ml | Problem statement: Evaluation evidence · Kickoff p. 12 | Set descriptions | Pending |
| REQ-0022 | Metrics with n, case mix, versions, and variability; include failures | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 5; Evaluation evidence | Metrics report | Pending |
| REQ-0031 | Only approved data; label each source (real, synthetic, team-generated) | P0 | All | Data Engineering | data | Problem statement: Data and execution boundaries | Source inventory | Pending |
| REQ-0018 | Real incremental processing (late arrivals, duplicates, changing schema) or, if data is static, labeled fixture | P1 | All | Data Engineering | data | Problem statement: Architecture freedom | Update fixture | Pending |
| REQ-0019 | Experiment tracking: model and prompt versions, parameters, metrics | P1 | All | Machine Learning | ml | Kickoff p. 20 | Experiment log | Pending |
| REQ-0024 | Breakdown by language, country, and segment; separate offline, simulation, and projection | P1 | All | Data Analytics | analysis | Problem statement: Evaluation evidence | Metrics report | Pending |
| REQ-0050 | Monitoring by country (latency, failures, escalations, complaints) | P1 | All | Data Analytics | analysis | Own: [analysis](../build/areas/analysis.md#country-monitoring) | Report by country | Pending |
| REQ-0023 | If there is an LLM judge: documented rubric validated against a human sample | P2 | If applicable | Machine Learning | ml | Problem statement: Evaluation evidence | Rubric + validated sample | Pending |

## Delivery (E)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0034 | Public repository `factored-hackathon-2026-[team]`, without secrets or restricted data | P0 | All | Rationale | all | Kickoff p. 18 | Repo link | Pending |
| REQ-0035 | Link to the deployed tool, with usage and spending limits | P0 | All | AI Engineering | ai | Kickoff p. 18 | Link | Pending |
| REQ-0036 | 4-to-6-slide presentation | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#presentation) | Pending |
| REQ-0037 | Short video pitch: demo and architecture decisions | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#video-pitch) | Pending |
| REQ-0051 | Repo README, presentation (4 to 6 slides), video script, AND `docs/` and `team/` all in English | P0 | All | Rationale | all | Own: [language](../build/delivery.md#language) | [Pre-submission check](../build/delivery.md#language) | Pending |
| REQ-0013 | Report data and language-coverage limitations | P0 | All | Rationale | analysis | Problem statement: Scope · Kickoff p. 15 | Limitations section | Pending |
| REQ-0030 | Declare what is missing: capacity, data, languages, deployment, risks | P0 | All | Rationale | all | Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 | Limitations section | Pending |

## Future work (not requirements)

- Expansion to other Latin American countries. The design makes it easier with REQ-0049 (country as configuration); it would require data, rules, currency, and tests for each new country.
- Streaming: only if a flow needs seconds-level freshness.

## Open questions

- Which flow do we choose? (Mon 9/28). This confirms or discards the flow-dependent requirements.
- How do we build the reference labels for evaluation (which cases require a human)?
