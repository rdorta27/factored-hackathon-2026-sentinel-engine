# Requirements

What the system must do to meet the hackathon brief. Each requirement has an ID (`REQ-####`) that the rest of the documentation cites, and this table doubles as the traceability matrix: every requirement is tied to the official document it comes from, the evaluation criterion it serves, the area that owns it, the evidence that will prove it, and its status.

**Purpose:** prioritize the work, spot evaluation criteria that still lack evidence, and see what blocks what ([dependencies](#dependencies)). **Related:** [The Challenge](../understand/overview.md), [dataset](../understand/dataset.md), [glossary](../understand/glossary/).

## Hackathon material

Requirements come from four official documents, plus clarifications published in the help channel. Except for the data dictionary, kept as a column-level reference in [understand/reference/](../understand/reference/), they are not in the repository; each teammate keeps a copy, and we cite them by section or page.

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
| P0 | 41 | 18 | 16 | 7 | 44% |
| P1 | 12 | 6 | 3 | 3 | 50% |
| P2 | 4 | 1 | 0 | 3 | 25% |
| **Total** | **57** | 25 | 19 | 13 | 44% |

## Functional (F)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0001 | Keep conversation context | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Conversation state per session (turns, candidates, pending confirmation, language) persisted in SQLite and restored after a restart (`tests/test_state_sqlite.py::test_session_conversation_and_case_survive_a_restart`); per-turn history in the handoff (`tests/test_handoff_package.py`); router context behind `ModelPort` (`tests/test_ai_router.py`) | Done |
| REQ-0002 | Clarify ambiguous requests or abstain from unsupported ones | P0 | All | AI Engineering | ai | Problem statement: Scope; What your solution should demonstrate 2 · Kickoff p. 11 | `clarification` with ranked candidates and out-of-scope handoff (`tests/test_contract.py::test_normal_case_variants_match_the_contract`, adversarial group E in `evidence/adversarial/20261001T130342Z/summary.json`); ambiguous cases replayed in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | Done |
| REQ-0003 | Answer only with verified records; if the data does not exist, say so | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 13 | Every amount and merchant in a reply is a verified Gold fact (`tests/test_facts_grounding.py`, mutation-checked); canary `test_rendered_facts_change_when_gold_changes`; case number only after read-back (`tests/test_contract.py`) | Done |
| REQ-0004 | Use tools safely to execute the flow; no real movement of money or live decisions (simulated actions only) | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2; Data and execution boundaries · Kickoff p. 11 | Session-bound tool port; writes only after the confirm box, idempotent, read back; `source=mock` and `noFundsHeld` on every confirmation; no write path skips confirmation (`tests/test_disputes_api.py`, adversarial D6 in `evidence/adversarial/20261001T130342Z/summary.json`) | Done |
| REQ-0006 | Define what it answers alone, what requires confirmation, and when to escalate | P0 | All | Rationale | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11 | [Conversation](../build/conversation.md) + policy engine + confirm box; handoff on person insist, unverified write, out of scope, unknown charge. Fraud and high-amount thresholds (decisions 25, 26) still null: proposed for a separate branch | In progress |
| REQ-0008 | Structured JSON handoff: request, verified facts, actions, evidence, open questions; no raw transcript | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14 | `handoff` reply carries the package: request, deterministic conversation summary and per-turn entries, verified facts, every action attempted across the session (failed ones included), evidence, open questions, language, country; no `customer_id`, no raw text; filed as an escalated case and read by the advisor at `GET /api/v1/handoffs` (`tests/test_handoff_package.py`, `tests/test_handoffs_api.py`) | Done |
| REQ-0009 | Demo: normal case resolved per policies | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Normal case in es-419 and pt-BR: confirm box → verified `case_confirmation` (`tests/test_contract.py`, `tests/test_facts_grounding.py`); replayed in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json`. Video: REQ-0037 | Done |
| REQ-0010 | Demo: ambiguous or unsupported case (clarifies or abstains) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Ambiguous charge → `clarification` with candidates; out of scope → handoff; nothing opened (`tests/adversarial/test_e_ambiguity.py`, `evidence/evaluation-runs/2024Q4-eval-v5/summary.json`). Video: REQ-0037 | Done |
| REQ-0011 | Demo: case requiring a human (escalates with handoff) | P0 | All | AI Engineering | ai | Problem statement: Scope · Kickoff p. 11 | Person insist and unverified write → `handoff` with package, filed as a ticket the advisor reads (`tests/test_handoffs_api.py`, `tests/test_handoff_package.py`). Video: REQ-0037 | Done |
| REQ-0012 | Robust interactions in Spanish and Portuguese; the dataset is Spanish-only, so pt-BR cases are team-generated and labeled as such | P0 | All | AI Engineering / ML | ai, ml | Problem statement: Scope · Kickoff p. 10 · Dataset summary | pt-BR demo + metrics by language + router pt-BR detection (`tests/test_ai_router.py`) | In progress |
| REQ-0033 | Policy decides, the LLM converses: it neither approves nor invents rules. The source's risk/eligibility separation is credit-specific and does not apply to disputes | P0 | All | AI Engineering / ML | ai, ml | Problem statement: Data and execution boundaries; What your solution should demonstrate 3 | Architecture | Done |
| REQ-0038 | Simple frontend for using the system (e.g., chat); dashboard not required (scope decision: no dashboard) | P0 | All | AI Engineering | ai | Kickoff p. 20 | One page served at `/ui/` by the same process: customer chat (confirm box, chips, transactions panel, handoff card) and the read-only advisor view (`tests/test_ui.py`, `tests/test_contract.py::test_served_app_is_the_full_app`); no dashboard ([009](../build/decisions/009-demo-ui-and-advisor-view.md)) | Done |
| REQ-0039 | Declare data freshness ("updated through…"); never claim anything more recent | P0 | All | AI Engineering / Data Engineering | ai, data | Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) · Dataset summary (data ends 2026-06-17) | `as_of` on the listing and `referenceDate` on every confirmation, one configurable reference date (`test_screen_and_engine_share_the_default_reference_date`, `tests/test_contract.py`) | Done |
| REQ-0040 | Request to speak to a person: a single offer to help and, if they insist, escalate immediately | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person) | One offer, then handoff (`tests/test_ui.py::test_agent_control_is_two_step_and_session_is_not_stored`). Gap: a person request while a confirm box is pending gets a clarification instead | In progress |
| REQ-0041 | Show amounts in the transaction's original currency; language follows the customer, currency follows the account | P0 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) · Dataset summary (local currency and USD) | COP/ARS per-customer tests `test_cop_customer_sees_only_cop_charges`, `test_ars_customer_sees_only_ars_charges`; pt-BR conversation keeps the charge currency (`tests/test_facts_grounding.py`) | Done |
| REQ-0042 | Open disputes with minimum effort: show candidate transactions instead of asking for amounts | P1 | Disputes | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-dispute) | Clarification chips and transactions-panel tap select exactly one charge without opening (`tests/test_chat.py`, `tests/test_contract.py`) | Done |
| REQ-0043 | Check the charge status (Pending, Reversed) before opening a dispute | P1 | Disputes, accounts | AI Engineering | ai | Own: [conversation](../build/conversation.md#when-opening-a-dispute) | Pending, Reversed and Declined explained, never disputed; raw `Refunded` mapped to Reversed (`tests/test_transactions.py`, `tests/test_disputes_api.py::test_preview_runs_the_policy`) | Done |
| REQ-0044 | Neutral Spanish, with local acronyms and terms explained; understand terms from other countries | P1 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#language) | Demo | Pending |
| REQ-0045 | Offer recent app-error context as a question (auxiliary context, not its own flow) | P2 | All | AI Engineering | ai | Own: [conversation](../build/conversation.md#app-context) | Demo | Pending |
| REQ-0046 | Route the handoff to an advisor with the right language and specialty (simulated) | P2 | All | AI Engineering | ai | Own: [AI](../build/areas/ai.md#simulated-routing) | Handoff example | Pending |

## Non-functional (NF)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0005 | Report only verified actions (timeout is not success) | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 2 · Kickoff p. 11 | Tool-failure test | Done |
| REQ-0007 | Permissions and policies in code, in addition to the prompt | P0 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13 | Policy in code; roles enforced in code (customer endpoints `customer`, `/api/v1/handoffs` `advisor`, 403 + `access_denied`); adversarial groups B, C, D in `evidence/adversarial/20261001T130342Z/summary.json` | Done |
| REQ-0021 | Failure tests: bad or missing data, expired session, unauthorized access, prompt injection, tool failure, multilingual ambiguity | P0 | All | Machine Learning | ml, ai | Problem statement: What your solution should demonstrate 5 · Kickoff p. 13 | Adversarial set `tests/adversarial/`: 36 attacks (chat, the disputes API and the advisor endpoint), `unsafe_outcome_rate` `0/36`, 28 `blocked_verified`, 3 `passes_on_mock`, 4 `no_defense_yet` (xfail strict), 1 `documented`, plus 5 covered elsewhere — `evidence/adversarial/20261001T130342Z/summary.json` — plus runner fault injection (gold, session, tool) degrading safely in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | Done |
| REQ-0027 | Authentication with test session, per-customer access control, retention policy | P0 | All | AI Engineering / Data Engineering | ai, data | Problem statement: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15 | Password login on `/api/v1/auth/*` (no login by customer number alone); isolation matrix `test_foreign_access_attempts_are_blocked_8_of_8`; `me` returns role and country only; sessions and conversation in SQLite keyed by token hash, conversation deleted on logout and expiry (`tests/test_state_sqlite.py`); retention table in the [specification](../architecture/specification.md#data-retention) | Done |
| REQ-0028 | Reproducibility: setup, versioning, repeatable evaluation | P0 | All | Rationale | all | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | stdlib evidence scripts with `verify` (`evidence/evaluation/eval_measure.py`), frozen write-once runs, offline replayable harness (`python3 -m eval.freeze`); full data-sync setup note pending | In progress |
| REQ-0047 | The LLM receives no identifiers or personal data (PII), and no restricted data goes in external model requests; tools filter by the session customer | P0 | All | AI Engineering | ai | Problem statement: Data and execution boundaries · Own: [security](../build/security.md#llm-visibility) | Session-bound lookup (`lookup_transactions` takes no customer arg) + 8/8 denial test (PR #16) + auth events as salted `session_ref` records with no IP (`test_audit_session_ref_is_a_hash_not_the_customer`) + router request whitelist (`tests/test_ai_router.py`). Adversarial set `evidence/adversarial/20261001T130342Z/summary.json`; the orchestrator sees an opaque customer hash, never the id; the free-text PII path `A9` stays `no_defense_yet` (masking, decision 004) | In progress |
| REQ-0048 | Decision order: policy in code > learned component > LLM | P0 | All | Rationale / ML | ai, ml | Problem statement: introduction · Kickoff p. 11 · Own: [system](../architecture/specification.md#decision-priority) | [Decision priority](../architecture/specification.md#decision-priority) | Done |
| REQ-0056 | Explicit trade-offs across autonomy, accuracy, latency, cost, and human oversight; justify where AI is used and where deterministic logic is preferable | P0 | All | Rationale | all | Problem statement: introduction · Kickoff p. 11 | Decisions + presentation | In progress |
| REQ-0025 | Observability: execution traces and logs, with country and language | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | `app/observability/` per-step + turn records with country and language, replay by `trace_id` (`test_full_turn_is_replayable_by_trace_id`); runner reads records by trace id in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | Done |
| REQ-0026 | Bounded retries, safe fallback; idempotent actions | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 | Tool-failure test | Done |
| REQ-0029 | Explanations based on sources, rules, and logs; not on model reasoning | P1 | All | AI Engineering | ai | Problem statement: What your solution should demonstrate 6 | `policy_rule` on every decide record and in the handoff evidence; summary built from turn codes, never model reasoning (`tests/test_handoff_package.py`) | Done |
| REQ-0032 | Mock tools with documented contracts and limitations | P1 | All | AI Engineering | ai | Problem statement: Data and execution boundaries | Tool and Gold contracts in the [specification](../architecture/specification.md#tool-contracts); mock and DuckDB Gold behind one seam with fallback (`tests/test_gold_duckdb.py`); memory and SQLite state behind the same ports; mocks listed in [demo architecture](../architecture/demo-architecture.md#mocked-components) | Done |
| REQ-0049 | Country is configuration, not code | P2 | All | Rationale | ai | Own: [AI](../build/areas/ai.md#technical-rules) | Configuration file | Done |

## Data and ML (DML)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0014 | Data-backed problem, with reproducible analysis justifying the flow | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 1 · Kickoff p. 13 | Reproducible analysis | Done |
| REQ-0015 | Repeatable pipeline with strict contracts, quality, lineage, and freshness; handles the declared ~2% duplicates, ~5% nulls and orphaned records | P0 | All | Data Engineering | data | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Dataset summary · Dictionary | Pipeline + quality report | In progress |
| REQ-0016 | At least one learned component compared against a baseline on held-out; a prompted or fine-tuned LLM counts if defined, evaluated and justified | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Help channel (9/28) | Router vs baseline on identical held-out cases plus system replay in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json`; fixtures are baseline-mirrored so the delta is zero by construction | In progress |
| REQ-0017 | Valid labels with no data leakage; justify metrics, thresholds, and splits | P0 | All | Machine Learning | ml | Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 | Window 2024Q4 with held-out cut 2025-07-01 enforced in code (`evidence/evaluation/method.md`); leak check 5611/5611 in `2024Q4-v1/summary.json`; team-written cases with dev/held_out splits and no shared ids in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | In progress |
| REQ-0020 | Baseline and system on the same held-out, with realistic distribution | P0 | All | Machine Learning | ml | Problem statement: Evaluation evidence · Kickoff p. 12 | Same 35 team-written cases for both models and the loop in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json`; held_out measured once | In progress |
| REQ-0022 | Metrics with n, case mix, versions, and variability; include failures | P0 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 5; Evaluation evidence | Every metric with n, mix, versions and failures in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | In progress |
| REQ-0055 | Report the mandatory outcome metrics: safe automated resolution (plus share attempted), containment, escalation quality (missed and unnecessary transfers), unsafe outcomes with counts and denominators, p50/p95 latency, cost per attempted case and per successful resolution ("not defined" if none) | P0 | All | Data Analytics | analysis, ml | Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12 | [Metrics](../build/metrics.md) report; router emits tokens and cost per turn (`tests/test_ai_router.py`); full mandatory set with denominators in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | In progress |
| REQ-0053 | Sizing and its limits: disputes per day in the data, capacity the prototype is designed for, and what changes at real volume | P0 | All | Data Analytics | analysis | Help channel (9/28) | Sizing section | In progress |
| REQ-0057 | Intended customer and business outcomes, with cost-per-resolution ROI against the baseline; projected savings labeled as projections | P1 | All | Data Analytics | analysis | Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13 | Cost per attempted/resolution measured in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` ("not defined" without resolutions); ROI labeled projection | In progress |
| REQ-0031 | Only approved data under the published data-use terms; label each source (real, de-identified, synthetic, team-generated) | P0 | All | Data Engineering | data | Problem statement: Data and execution boundaries | Source inventory | Pending |
| REQ-0054 | External data only if justified: source, license, why it is needed, no PII, labeled as external | P1 | All | Data Engineering | data, ml | Help channel (9/28) | Source inventory | Pending |
| REQ-0018 | Real incremental processing of the declared late arrivals, duplicates and schema evolution; a labeled test fixture proves update correctness | P0 | All | Data Engineering | data | Problem statement: Architecture freedom · Dataset summary | Update fixture | Pending |
| REQ-0019 | Experiment tracking: model and prompt versions, parameters, metrics | P1 | All | Machine Learning | ml | Kickoff p. 20 | Router `describe` plus tokens and cost on the `understand` record (`tests/test_ai_router.py`); run versions model route prompt and label provenance in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json` | In progress |
| REQ-0024 | Breakdown by language, country, and authorized segment, investigating disparities (fairness) and stating small-sample limits; separate offline, simulation, and projection | P1 | All | Data Analytics | analysis | Problem statement: Evaluation evidence | Metrics by locale and country with small-sample limits in `evidence/evaluation-runs/2024Q4-eval-v5/summary.json`; team-written simulation, offline only | In progress |
| REQ-0050 | Monitoring by country (latency, failures, escalations, complaints) | P1 | All | Data Analytics | analysis | Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring) | Report by country | Pending |
| REQ-0023 | If there is an LLM judge: documented rubric validated on a sample against human or deterministic judgments | P2 | If applicable | Machine Learning | ml | Problem statement: Evaluation evidence | Rubric + validated sample | Pending |

## Delivery (E)

| ID | Requirement | P | Flow | Criterion | Area | Source | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| REQ-0034 | Public repository `factored-hackathon-2026-[team]`, without secrets or restricted data; all links sent to `hackathon.admin@factored.ai` | P0 | All | Rationale | all | Kickoff p. 18 | Repository `factored-hackathon-2026-sentinel-engine` is public; current tree has no bucket or account id. Pending: final secrets and data review, and the bucket id still present in older commits | In progress |
| REQ-0035 | Link to the deployed tool, with usage and spending limits; a minimal deployment is enough, cloud is not mandatory | P0 | All | AI Engineering | ai | Kickoff p. 18 · Help channel (9/28) | Link | Pending |
| REQ-0036 | 4-to-6-slide presentation | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#presentation) | Pending |
| REQ-0037 | Short, mandatory video pitch: working demo and core architecture decisions | P0 | All | Rationale | all | Kickoff p. 18 | [Script](../build/delivery.md#video-pitch) | Pending |
| REQ-0051 | Repo README, presentation (4 to 6 slides), video script, AND `docs/` and `team/` all in English | P0 | All | Rationale | all | Own: [language](../build/delivery.md#language) | [Pre-submission check](../build/delivery.md#language) | Pending |
| REQ-0013 | Report data and language-coverage limitations, including that the dataset has no Portuguese text and covers only MX, CO and AR | P0 | All | Rationale | analysis | Problem statement: Scope · Kickoff p. 15 · Dataset summary | Limitations section | Pending |
| REQ-0030 | Declare what is missing: capacity, data, languages, deployment, risks | P0 | All | Rationale | all | Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 · Help channel (9/28) | Limitations section | In progress |
| REQ-0052 | Credible path to production: how it deploys, scales, is monitored and secured, and what changes from the prototype | P0 | All | AI Engineering / Rationale | ai, all | Help channel (9/28) · Kickoff p. 15 | [Path to production](../architecture/specification.md#path-to-production) | In progress |

## Dependencies

A requirement depends on another when it cannot be met, or its evidence cannot be produced, until the other one is met. Only direct dependencies are listed; requirements not listed (REQ-0025, REQ-0027, REQ-0031, REQ-0032, REQ-0049) depend on none. Update this table when a requirement is added or its evidence changes.

| Requirement | Depends on | Why |
|---|---|---|
| REQ-0001 | REQ-0027 | Context is kept per authenticated session |
| REQ-0002 | REQ-0001, REQ-0003 | Clarifying needs the conversation so far and the verified candidates |
| REQ-0003 | REQ-0015, REQ-0032 | Verified facts come from Gold through the tool contracts |
| REQ-0004 | REQ-0005, REQ-0007, REQ-0032 | Safe tool use needs read-back, permissions in code and documented mock tools |
| REQ-0006 | REQ-0007, REQ-0033 | The answer/confirm/escalate split is policy in code |
| REQ-0008 | REQ-0003, REQ-0029, REQ-0047 | The package carries verified facts, rule-based evidence and no PII |
| REQ-0009 | REQ-0003, REQ-0004, REQ-0006, REQ-0012 | The normal case uses verified data, safe tools and policy, in both languages |
| REQ-0010 | REQ-0002 | Demo of the clarify-or-abstain behaviour |
| REQ-0011 | REQ-0008, REQ-0040 | Demo of the handoff and the person request |
| REQ-0012 | REQ-0001 | Language is detected and kept in the conversation state |
| REQ-0033 | REQ-0048 | Applies the decision order |
| REQ-0038 | REQ-0027 | The page runs on the test session |
| REQ-0039 | REQ-0015 | Freshness comes from the pipeline's as-of date |
| REQ-0040 | REQ-0006 | A person request is one of the escalation rules |
| REQ-0041 | REQ-0003 | Currency is a verified fact of the transaction |
| REQ-0042 | REQ-0003, REQ-0038 | Candidates are verified charges shown in the page |
| REQ-0043 | REQ-0003, REQ-0015 | Charge status is a verified Gold field |
| REQ-0044 | REQ-0012 | Extends the Spanish support |
| REQ-0045 | REQ-0001 | App-error context is offered inside the conversation |
| REQ-0046 | REQ-0008, REQ-0012 | Routes the package by language |
| REQ-0005 | REQ-0032 | Read-back uses the tool contracts |
| REQ-0007 | REQ-0027 | Roles and per-customer checks need the session |
| REQ-0021 | REQ-0007, REQ-0012, REQ-0026, REQ-0027 | The attacks test permissions, languages, fallback and the session |
| REQ-0026 | REQ-0005 | Retries are safe only when success is verified |
| REQ-0028 | REQ-0015, REQ-0019 | Reproducible pipeline and versioned runs |
| REQ-0029 | REQ-0025 | Explanations cite the logged rules and sources |
| REQ-0047 | REQ-0027 | Tools filter by the session customer |
| REQ-0048 | REQ-0016 | The order needs a learned component in between |
| REQ-0056 | REQ-0016, REQ-0055 | Trade-offs are argued with the measured metrics |
| REQ-0014 | REQ-0031 | The analysis uses approved, labelled data |
| REQ-0015 | REQ-0031 | The pipeline ingests approved, labelled data |
| REQ-0016 | REQ-0017, REQ-0020 | Comparison needs valid labels and a shared held-out |
| REQ-0017 | REQ-0015 | Labels come from the pipeline output |
| REQ-0018 | REQ-0015 | Incremental processing extends the pipeline |
| REQ-0019 | REQ-0016 | Tracks the learned component's versions |
| REQ-0020 | REQ-0017 | Held-out built on valid labels |
| REQ-0022 | REQ-0020, REQ-0055 | Reports the held-out metrics with n and failures |
| REQ-0023 | REQ-0016 | Only applies to an LLM component being judged |
| REQ-0024 | REQ-0012, REQ-0022 | Breakdown of the reported metrics by language and country |
| REQ-0050 | REQ-0024, REQ-0025 | Country monitoring reads the logs and the breakdown |
| REQ-0053 | REQ-0014 | Sizing uses the dispute volumes from the analysis |
| REQ-0054 | REQ-0031 | Same source inventory |
| REQ-0055 | REQ-0020, REQ-0025 | Metrics on the held-out, latency and cost from the logs |
| REQ-0057 | REQ-0055 | ROI uses cost per resolution |
| REQ-0013 | REQ-0012, REQ-0024 | Coverage limits come from the language support and the breakdown |
| REQ-0030 | REQ-0013, REQ-0053 | Gathers the data, language and capacity limits |
| REQ-0034 | REQ-0031 | No restricted data in the public repo |
| REQ-0035 | REQ-0027, REQ-0034 | A public link needs the session and a clean repo |
| REQ-0036 | REQ-0055, REQ-0056 | Slides present metrics and trade-offs |
| REQ-0037 | REQ-0009, REQ-0010, REQ-0011, REQ-0035 | The video shows the three demo cases on the deployed tool |
| REQ-0051 | REQ-0036, REQ-0037 | Language check covers the slides and video script |
| REQ-0052 | REQ-0025, REQ-0050 | Path to production includes monitoring |

Chains that still block P0 work:

- **Data:** REQ-0031 (Pending) → REQ-0015 (In progress) → REQ-0017 → REQ-0020 → REQ-0016, REQ-0022, REQ-0055. REQ-0018 also waits on REQ-0015.
- **Deployment and video:** REQ-0034 → REQ-0035 (Pending) → REQ-0037 → REQ-0051.
- **Slides:** REQ-0055 → REQ-0056 → REQ-0036 → REQ-0051.
- **Limitations:** REQ-0012, REQ-0024 → REQ-0013 → REQ-0030.

## Future work (not requirements)

- Expansion to other Latin American countries. The design makes it easier with REQ-0049 (country as configuration); it would require data, rules, currency, and tests for each new country.
- Streaming: only if a flow needs seconds-level freshness.

## Open questions

None open: reference labels are team-written simulation cases plus the frozen
data label universe (`evidence/evaluation/2024Q4-v1/summary.json`); human-required
cases are the `requires_handoff` ones in `sentinel-ai-core/eval/cases/`.
