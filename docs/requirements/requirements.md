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
| **Depends on** | Requirements that must be met first (see [dependencies](#dependencies)) |

Each section has a summary table and, below it, one card per requirement with its description, source, dependencies and evidence. **Evidence** says what proves the requirement today (*Proven by*) and what is still needed (*Missing*).

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

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0001](#req-0001) | Keep conversation context | P0 | ai | [REQ-0027](#req-0027) | Done |
| [REQ-0002](#req-0002) | Clarify or abstain | P0 | ai | [REQ-0001](#req-0001), [REQ-0003](#req-0003) | Done |
| [REQ-0003](#req-0003) | Answer only from verified records | P0 | ai | [REQ-0015](#req-0015), [REQ-0032](#req-0032) | Done |
| [REQ-0004](#req-0004) | Use tools safely, simulated actions only | P0 | ai | [REQ-0005](#req-0005), [REQ-0007](#req-0007), [REQ-0032](#req-0032) | Done |
| [REQ-0006](#req-0006) | Decide answer, confirm or escalate | P0 | ai | [REQ-0007](#req-0007), [REQ-0033](#req-0033) | In progress |
| [REQ-0008](#req-0008) | Structured handoff package | P0 | ai | [REQ-0003](#req-0003), [REQ-0029](#req-0029), [REQ-0047](#req-0047) | Done |
| [REQ-0009](#req-0009) | Demo: normal case | P0 | ai | [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012) | Done |
| [REQ-0010](#req-0010) | Demo: ambiguous or unsupported case | P0 | ai | [REQ-0002](#req-0002) | Done |
| [REQ-0011](#req-0011) | Demo: case requiring a human | P0 | ai | [REQ-0008](#req-0008), [REQ-0040](#req-0040) | Done |
| [REQ-0012](#req-0012) | Works in Spanish and Portuguese | P0 | ai, ml | [REQ-0001](#req-0001) | In progress |
| [REQ-0033](#req-0033) | Policy decides, the LLM converses | P0 | ai, ml | [REQ-0048](#req-0048) | Done |
| [REQ-0038](#req-0038) | Simple frontend | P0 | ai | [REQ-0027](#req-0027) | Done |
| [REQ-0039](#req-0039) | Declare data freshness | P0 | ai, data | [REQ-0015](#req-0015) | Done |
| [REQ-0040](#req-0040) | Request for a person | P0 | ai | [REQ-0006](#req-0006) | In progress |
| [REQ-0041](#req-0041) | Original currency, customer's language | P0 | ai | [REQ-0003](#req-0003) | Done |
| [REQ-0042](#req-0042) | Minimum-effort dispute opening | P1 | ai | [REQ-0003](#req-0003), [REQ-0038](#req-0038) | Done |
| [REQ-0043](#req-0043) | Check charge status first | P1 | ai | [REQ-0003](#req-0003), [REQ-0015](#req-0015) | Done |
| [REQ-0044](#req-0044) | Neutral Spanish with local terms | P1 | ai | [REQ-0012](#req-0012) | Pending |
| [REQ-0045](#req-0045) | App-error context | P2 | ai | [REQ-0001](#req-0001) | Pending |
| [REQ-0046](#req-0046) | Handoff routing (simulated) | P2 | ai | [REQ-0008](#req-0008), [REQ-0012](#req-0012) | Pending |

<a id="req-0001"></a>
### REQ-0001 · Keep conversation context

The system remembers what was said earlier in the conversation (the charge under discussion, the pending confirmation, the language) so the customer never has to repeat it. The brief lists it first among the minimum behaviors of a functioning AI system.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0027](#req-0027). Context is kept per authenticated session.

**Evidence:** Proven by: conversation state per session (turns, candidates, pending confirmation, language) stored in SQLite and restored after a restart (`tests/test_state_sqlite.py::test_session_conversation_and_case_survive_a_restart`); per-turn history carried in the handoff (`tests/test_handoff_package.py`); router context behind `ModelPort` (`tests/test_ai_router.py`).

<a id="req-0002"></a>
### REQ-0002 · Clarify or abstain

When a request is ambiguous (several charges match) the system asks a question instead of guessing; when it is out of scope it says so and offers a person. It never acts on a guess. This is the "ambiguous or unsupported" demo case.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope; What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0001](#req-0001), [REQ-0003](#req-0003). Clarifying needs the conversation so far and the verified candidates.

**Evidence:** Proven by: `clarification` replies with ranked candidates and the out-of-scope handoff (`tests/test_contract.py::test_normal_case_variants_match_the_contract`); adversarial group E in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json); ambiguous cases replayed in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

<a id="req-0003"></a>
### REQ-0003 · Answer only from verified records

Every fact in a reply (amount, merchant, date, case number) must come from the customer's own records, never from the model. If the record does not exist, the system says so instead of inventing it.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 13

**Depends on:** [REQ-0015](#req-0015), [REQ-0032](#req-0032). Verified facts come from Gold through the tool contracts.

**Evidence:** Proven by: every amount and merchant in a reply is checked against the session customer's Gold rows (`tests/test_facts_grounding.py`, mutation-checked); canary `test_rendered_facts_change_when_gold_changes`; a case number is shown only after it is read back (`tests/test_contract.py`).

<a id="req-0004"></a>
### REQ-0004 · Use tools safely, simulated actions only

The system acts only through tools bound to the logged-in customer, asks for confirmation before any write, and never moves money: every action is simulated and labeled as such.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2; Data and execution boundaries · Kickoff p. 11

**Depends on:** [REQ-0005](#req-0005), [REQ-0007](#req-0007), [REQ-0032](#req-0032). Safe tool use needs read-back, permissions in code and documented mock tools.

**Evidence:** Proven by: session-bound tools; writes only after the confirm box, idempotent and read back; `source=mock` and `noFundsHeld` on every confirmation; no write path skips confirmation (`tests/test_disputes_api.py`, adversarial D6 in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json)).

<a id="req-0006"></a>
### REQ-0006 · Decide answer, confirm or escalate

Written rules say what the system answers alone, which actions need the customer's confirmation, and when it must hand over to a person. The brief calls this controlled automation.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11

**Depends on:** [REQ-0007](#req-0007), [REQ-0033](#req-0033). The answer/confirm/escalate split is policy in code.

**Evidence:** Proven by: the [conversation rules](../build/conversation.md), the policy engine and the confirm box; handoff on person insist, unverified write, out of scope and unknown charge.

Missing: the fraud and high-amount thresholds (decisions 25, 26) are still null.

<a id="req-0008"></a>
### REQ-0008 · Structured handoff package

When the system escalates, the advisor receives a structured JSON package with the request, the verified facts, the actions attempted, the evidence and the open questions, not the raw transcript.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14

**Depends on:** [REQ-0003](#req-0003), [REQ-0029](#req-0029), [REQ-0047](#req-0047). The package carries verified facts, rule-based evidence and no PII.

**Evidence:** Proven by: the `handoff` reply carries request, a deterministic summary, per-turn entries, verified facts, every action attempted (failed ones included), evidence, open questions, language and country, with no `customer_id` and no raw text; it is filed as an escalated case the advisor reads at `GET /api/v1/handoffs` (`tests/test_handoff_package.py`, `tests/test_handoffs_api.py`).

<a id="req-0009"></a>
### REQ-0009 · Demo: normal case

The first of the three mandatory demo cases: a customer asks about a charge and the system resolves it end to end according to policy (here, opening a verified dispute).

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012). The normal case uses verified data, safe tools and policy, in both languages.

**Evidence:** Proven by: the confirm box leads to a verified `case_confirmation` (`tests/test_contract.py`, `tests/test_facts_grounding.py`); replayed in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: shown in the video (REQ-0037).

<a id="req-0010"></a>
### REQ-0010 · Demo: ambiguous or unsupported case

The second mandatory demo case: a request the system cannot resolve as stated, where it clarifies or abstains without acting.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0002](#req-0002). Demo of the clarify-or-abstain behaviour.

**Evidence:** Proven by: an ambiguous charge produces a `clarification` with candidates and an out-of-scope request a handoff, with nothing opened (`tests/adversarial/test_e_ambiguity.py`, [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json)).

Missing: shown in the video (REQ-0037).

<a id="req-0011"></a>
### REQ-0011 · Demo: case requiring a human

The third mandatory demo case: a request the system must not handle alone, escalated with the handoff package.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0008](#req-0008), [REQ-0040](#req-0040). Demo of the handoff and the person request.

**Evidence:** Proven by: a person insist and an unverified write produce a `handoff` with its package, filed as a ticket the advisor reads (`tests/test_handoffs_api.py`, `tests/test_handoff_package.py`).

Missing: shown in the video (REQ-0037).

<a id="req-0012"></a>
### REQ-0012 · Works in Spanish and Portuguese

The system must serve customers in Spanish and in Portuguese (brief: Scope; kickoff p. 10). There is no Portuguese in the data: the dataset is Spanish only and covers MX, CO and AR, so the system must work in Portuguese without data to learn from, and any Portuguese test material is team-generated and labeled as such.

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering / ML · **Area:** ai, ml

**Source:** Problem statement: Scope · Kickoff p. 10 · Dataset summary

**Depends on:** [REQ-0001](#req-0001). Language is detected and kept in the conversation state.

**Evidence:** Proven by: Spanish (es-419) on the whole demo path; router language detection includes pt-BR (`tests/test_ai_router.py`).

Missing: how the system serves a Portuguese-speaking customer is not defined yet (replies, country and currency when no Brazilian customer exists). The eval holds 13 single-turn pt-BR utterances written by the team, unreviewed and attached to MX and CO customers; they are not yet a valid test of Portuguese.

<a id="req-0033"></a>
### REQ-0033 · Policy decides, the LLM converses

The model talks to the customer but never approves anything or invents rules; decisions come from policy code. The brief's separation of risk and eligibility is specific to credit and does not apply to disputes.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / ML · **Area:** ai, ml

**Source:** Problem statement: Data and execution boundaries; What your solution should demonstrate 3

**Depends on:** [REQ-0048](#req-0048). Applies the decision order.

**Evidence:** Proven by: the architecture, where only the policy engine decides.

<a id="req-0038"></a>
### REQ-0038 · Simple frontend

A simple way to use the system, such as a chat page. A dashboard is not required, and we chose not to build one.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 20

**Depends on:** [REQ-0027](#req-0027). The page runs on the test session.

**Evidence:** Proven by: one page at `/ui/` served by the same process with the customer chat (confirm box, chips, transactions panel, handoff card) and the read-only advisor view (`tests/test_ui.py`, `tests/test_contract.py::test_served_app_is_the_full_app`); [009](../build/decisions/009-demo-ui-and-advisor-view.md).

<a id="req-0039"></a>
### REQ-0039 · Declare data freshness

Every answer about data says how current it is ("updated through ...") and never claims anything newer. The dataset ends on 2026-06-17.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / Data Engineering · **Area:** ai, data

**Source:** Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) · Dataset summary (data ends 2026-06-17)

**Depends on:** [REQ-0015](#req-0015). Freshness comes from the pipeline's as-of date.

**Evidence:** Proven by: `as_of` on the listing and `referenceDate` on every confirmation, from one configurable reference date (`test_screen_and_engine_share_the_default_reference_date`, `tests/test_contract.py`).

<a id="req-0040"></a>
### REQ-0040 · Request for a person

When the customer asks for a person, the system makes one offer to help and, if they insist, escalates at once.

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person)

**Depends on:** [REQ-0006](#req-0006). A person request is one of the escalation rules.

**Evidence:** Proven by: one offer, then handoff (`tests/test_ui.py::test_agent_control_is_two_step_and_session_is_not_stored`).

Missing: while a confirm box is pending, a person request gets a clarification instead of escalating.

<a id="req-0041"></a>
### REQ-0041 · Original currency, customer's language

Amounts are shown in the transaction's original currency; the language follows the customer and the currency follows the account.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#language) · Dataset summary (local currency and USD)

**Depends on:** [REQ-0003](#req-0003). Currency is a verified fact of the transaction.

**Evidence:** Proven by: COP and ARS isolation tests (`test_cop_customer_sees_only_cop_charges`, `test_ars_customer_sees_only_ars_charges`); a Portuguese conversation keeps the charge's currency (`tests/test_facts_grounding.py`).

<a id="req-0042"></a>
### REQ-0042 · Minimum-effort dispute opening

Show the customer their candidate charges to pick from instead of asking them to type amounts or dates.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai · **Flow:** Disputes

**Source:** Own: [conversation](../build/conversation.md#when-opening-a-dispute)

**Depends on:** [REQ-0003](#req-0003), [REQ-0038](#req-0038). Candidates are verified charges shown in the page.

**Evidence:** Proven by: clarification chips and a tap on the transactions panel select exactly one charge without opening anything (`tests/test_chat.py`, `tests/test_contract.py`).

<a id="req-0043"></a>
### REQ-0043 · Check charge status first

Before opening a dispute, check whether the charge is pending, reversed or declined, and explain instead of disputing.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai · **Flow:** Disputes, accounts

**Source:** Own: [conversation](../build/conversation.md#when-opening-a-dispute)

**Depends on:** [REQ-0003](#req-0003), [REQ-0015](#req-0015). Charge status is a verified Gold field.

**Evidence:** Proven by: Pending, Reversed and Declined are explained and never disputed; raw `Refunded` maps to Reversed (`tests/test_transactions.py`, `tests/test_disputes_api.py::test_preview_runs_the_policy`).

<a id="req-0044"></a>
### REQ-0044 · Neutral Spanish with local terms

Replies use neutral Latin American Spanish, explain local acronyms and understand terms from the other countries.

**Priority:** P1 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#language)

**Depends on:** [REQ-0012](#req-0012). Extends the Spanish support.

**Evidence:** Missing: the glossary applied in replies and a case with another country's term.

<a id="req-0045"></a>
### REQ-0045 · App-error context

If the customer recently had an error in the app, offer it as a question for context. It is auxiliary, not a flow of its own.

**Priority:** P2 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#app-context)

**Depends on:** [REQ-0001](#req-0001). App-error context is offered inside the conversation.

**Evidence:** Missing: not started.

<a id="req-0046"></a>
### REQ-0046 · Handoff routing (simulated)

Route the handoff to an advisor with the right language and specialty, simulated.

**Priority:** P2 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [AI](../build/areas/ai.md#simulated-routing)

**Depends on:** [REQ-0008](#req-0008), [REQ-0012](#req-0012). Routes the package by language.

**Evidence:** Missing: not started.

## Non-functional (NF)

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0005](#req-0005) | Report only verified actions | P0 | ai | [REQ-0032](#req-0032) | Done |
| [REQ-0007](#req-0007) | Permissions and policy in code | P0 | ai | [REQ-0027](#req-0027) | Done |
| [REQ-0021](#req-0021) | Failure tests | P0 | ml, ai | [REQ-0007](#req-0007), [REQ-0012](#req-0012), [REQ-0026](#req-0026), [REQ-0027](#req-0027) | Done |
| [REQ-0027](#req-0027) | Authentication, isolation and retention | P0 | ai, data | — | Done |
| [REQ-0028](#req-0028) | Reproducible setup | P0 | all | [REQ-0015](#req-0015), [REQ-0019](#req-0019) | In progress |
| [REQ-0047](#req-0047) | No personal data to the LLM | P0 | ai | [REQ-0027](#req-0027) | In progress |
| [REQ-0048](#req-0048) | Decision order | P0 | ai, ml | [REQ-0016](#req-0016) | Done |
| [REQ-0056](#req-0056) | Explicit trade-offs | P0 | all | [REQ-0016](#req-0016), [REQ-0055](#req-0055) | In progress |
| [REQ-0025](#req-0025) | Observability | P1 | ai | — | Done |
| [REQ-0026](#req-0026) | Bounded retries and safe fallback | P1 | ai | [REQ-0005](#req-0005) | Done |
| [REQ-0029](#req-0029) | Explanations from sources and rules | P1 | ai | [REQ-0025](#req-0025) | Done |
| [REQ-0032](#req-0032) | Documented mock tools | P1 | ai | — | Done |
| [REQ-0049](#req-0049) | Country as configuration | P2 | ai | — | Done |

<a id="req-0005"></a>
### REQ-0005 · Report only verified actions

The system tells the customer an action happened only after reading it back. A timeout or an error is never reported as success.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0032](#req-0032). Read-back uses the tool contracts.

**Evidence:** Proven by: tool-failure tests where a failed or unconfirmed write produces a handoff, not a success message (`lookup_dispute` read-back and the `verify` record).

<a id="req-0007"></a>
### REQ-0007 · Permissions and policy in code

Who can see or do what is enforced by code in the service, not by instructions in the prompt, so a manipulated model still cannot break the rules.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13

**Depends on:** [REQ-0027](#req-0027). Roles and per-customer checks need the session.

**Evidence:** Proven by: policy engine in code; roles enforced per route (customer routes need `customer`, `/api/v1/handoffs` needs `advisor`; a failure is a 403 recorded as `access_denied`); adversarial groups B, C and D in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json).

<a id="req-0021"></a>
### REQ-0021 · Failure tests

Test the cases the brief names explicitly: bad or missing data, expired session, unauthorized access, prompt injection, tool failure and multilingual ambiguity.

**Priority:** P0 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml, ai

**Source:** Problem statement: What your solution should demonstrate 5 · Kickoff p. 13

**Depends on:** [REQ-0007](#req-0007), [REQ-0012](#req-0012), [REQ-0026](#req-0026), [REQ-0027](#req-0027). The attacks test permissions, languages, fallback and the session.

**Evidence:** Proven by: 36 attacks in `tests/adversarial/` against the chat, the disputes API and the advisor endpoint, with `unsafe_outcome_rate` `0/36` in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json); runner fault injection (Gold, session, tool) degrading safely in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

<a id="req-0027"></a>
### REQ-0027 · Authentication, isolation and retention

A trusted test session proves identity (a customer number alone does not), each customer reaches only their own records, and personal and conversation data has a retention policy.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / Data Engineering · **Area:** ai, data

**Source:** Problem statement: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15

**Evidence:** Proven by: password login on `/api/v1/auth/*`; isolation matrix `test_foreign_access_attempts_are_blocked_8_of_8`; `me` returns role and country only; sessions and conversation stored by token hash and deleted on logout and expiry (`tests/test_state_sqlite.py`); [retention table](../architecture/specification.md#data-retention).

<a id="req-0028"></a>
### REQ-0028 · Reproducible setup

Anyone can set the project up, rerun the evaluation and get the same results, with versioned code and data runs.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Depends on:** [REQ-0015](#req-0015), [REQ-0019](#req-0019). Reproducible pipeline and versioned runs.

**Evidence:** Proven by: stdlib evidence scripts with `verify` (`evidence/evaluation/eval_measure.py`), write-once frozen runs, and an offline replayable harness (`python3 -m eval.freeze`).

Missing: the data-sync setup note.

<a id="req-0047"></a>
### REQ-0047 · No personal data to the LLM

The model never receives identifiers or personal data, and no restricted data goes into external model requests. Tools filter by the session customer instead.

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Data and execution boundaries · Own: [security](../build/security.md#llm-visibility)

**Depends on:** [REQ-0027](#req-0027). Tools filter by the session customer.

**Evidence:** Proven by: session-bound lookup that takes no customer argument plus the 8/8 denial test; auth events stored as salted `session_ref` records with no IP (`test_audit_session_ref_is_a_hash_not_the_customer`); router request whitelist (`tests/test_ai_router.py`); the orchestrator sees an opaque customer hash, never the id ([`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json)).

Missing: personal data typed in free text still reaches the model (attack `A9`, `no_defense_yet`); masking is decision 004.

<a id="req-0048"></a>
### REQ-0048 · Decision order

When sources disagree, policy in code wins over the learned component, which wins over the LLM.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale / ML · **Area:** ai, ml

**Source:** Problem statement: introduction · Kickoff p. 11 · Own: [system](../architecture/specification.md#decision-priority)

**Depends on:** [REQ-0016](#req-0016). The order needs a learned component in between.

**Evidence:** Proven by: the [decision priority](../architecture/specification.md#decision-priority) in the specification.

<a id="req-0056"></a>
### REQ-0056 · Explicit trade-offs

Explain the trade-offs between autonomy, accuracy, latency, cost and human oversight, and justify where AI is used and where deterministic logic is better.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: introduction · Kickoff p. 11

**Depends on:** [REQ-0016](#req-0016), [REQ-0055](#req-0055). Trade-offs are argued with the measured metrics.

**Evidence:** Proven by: the [decisions](../build/decisions/).

Missing: the argument with the final metrics, in the presentation.

<a id="req-0025"></a>
### REQ-0025 · Observability

Execution traces and logs for every turn, including country and language, so any conversation can be reconstructed.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Evidence:** Proven by: per-step and turn records in `app/observability/` with country and language, replay by `trace_id` (`test_full_turn_is_replayable_by_trace_id`); the runner reads records by trace id in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

<a id="req-0026"></a>
### REQ-0026 · Bounded retries and safe fallback

Retries have a limit, failures fall back to a safe outcome (usually a handoff), and repeating an action never duplicates it.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Depends on:** [REQ-0005](#req-0005). Retries are safe only when success is verified.

**Evidence:** Proven by: tool-failure tests, the `ModelUnavailable` fallback and idempotent dispute creation.

<a id="req-0029"></a>
### REQ-0029 · Explanations from sources and rules

Explanations cite data sources, policy rules and execution records. The model's hidden reasoning is not an audit artifact.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6

**Depends on:** [REQ-0025](#req-0025). Explanations cite the logged rules and sources.

**Evidence:** Proven by: `policy_rule` on every decide record and in the handoff evidence; the summary is built from turn codes, never from model reasoning (`tests/test_handoff_package.py`).

<a id="req-0032"></a>
### REQ-0032 · Documented mock tools

Mock banking tools are allowed if their contracts and limitations are documented.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Data and execution boundaries

**Evidence:** Proven by: tool and Gold contracts in the [specification](../architecture/specification.md#tool-contracts); mock and DuckDB Gold behind one seam with fallback (`tests/test_gold_duckdb.py`); memory and SQLite state behind the same ports; mocks listed in the [demo architecture](../architecture/demo-architecture.md#mocked-components).

<a id="req-0049"></a>
### REQ-0049 · Country as configuration

Country rules live in configuration files, so adding a country does not require new code.

**Priority:** P2 · **Status:** Done · **Criterion:** Rationale · **Area:** ai

**Source:** Own: [AI](../build/areas/ai.md#technical-rules)

**Evidence:** Proven by: per-country policy files in `sentinel-ai-core/config/policy/`.

## Data and ML (DML)

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0014](#req-0014) | Data-backed problem | P0 | analysis | [REQ-0031](#req-0031) | Done |
| [REQ-0015](#req-0015) | Repeatable pipeline with contracts | P0 | data | [REQ-0031](#req-0031) | In progress |
| [REQ-0016](#req-0016) | Learned component vs baseline | P0 | ml | [REQ-0017](#req-0017), [REQ-0020](#req-0020) | In progress |
| [REQ-0017](#req-0017) | Valid labels, no leakage | P0 | ml | [REQ-0015](#req-0015) | In progress |
| [REQ-0020](#req-0020) | Same held-out for baseline and system | P0 | ml | [REQ-0017](#req-0017) | In progress |
| [REQ-0022](#req-0022) | Metrics with n, mix and variability | P0 | analysis | [REQ-0020](#req-0020), [REQ-0055](#req-0055) | In progress |
| [REQ-0055](#req-0055) | Mandatory outcome metrics | P0 | analysis, ml | [REQ-0020](#req-0020), [REQ-0025](#req-0025) | In progress |
| [REQ-0053](#req-0053) | Sizing and its limits | P0 | analysis | [REQ-0014](#req-0014) | In progress |
| [REQ-0057](#req-0057) | Business outcomes and ROI | P1 | analysis | [REQ-0055](#req-0055) | In progress |
| [REQ-0031](#req-0031) | Approved data, labeled by origin | P0 | data | — | Pending |
| [REQ-0054](#req-0054) | Justified external data | P1 | data, ml | [REQ-0031](#req-0031) | Pending |
| [REQ-0018](#req-0018) | Real incremental processing | P0 | data | [REQ-0015](#req-0015) | Pending |
| [REQ-0019](#req-0019) | Experiment tracking | P1 | ml | [REQ-0016](#req-0016) | In progress |
| [REQ-0024](#req-0024) | Breakdown by language, country and segment | P1 | analysis | [REQ-0012](#req-0012), [REQ-0022](#req-0022) | In progress |
| [REQ-0050](#req-0050) | Monitoring by country | P1 | analysis | [REQ-0024](#req-0024), [REQ-0025](#req-0025) | Pending |
| [REQ-0023](#req-0023) | Validated LLM judge, if used | P2 | ml | [REQ-0016](#req-0016) | Pending |

<a id="req-0014"></a>
### REQ-0014 · Data-backed problem

Use the dataset to show the chosen flow matters: contact reasons, demand, data quality and operational constraints, in a reproducible analysis.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0031](#req-0031). The analysis uses approved, labeled data.

**Evidence:** Proven by: the reproducible [flow measurements](../build/flows/02-flow-measurements.md) and [flow selection](../build/flows/03-flow-selection.md).

<a id="req-0015"></a>
### REQ-0015 · Repeatable pipeline with contracts

A data preparation pipeline (Bronze, Silver, Gold) that runs the same way every time, enforces column contracts, checks quality, records lineage and freshness, and handles the dataset's declared issues: about 2% duplicates, 5% nulls and orphaned records.

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Dataset summary · Dictionary

**Depends on:** [REQ-0031](#req-0031). The pipeline ingests approved, labeled data.

**Evidence:** Proven by: pipeline code with tests in `sentinel-data-engine/`.

Missing: an end-to-end run and its quality report.

<a id="req-0016"></a>
### REQ-0016 · Learned component vs baseline

At least one learned component evaluated against a simpler baseline on held-out cases. A prompted LLM counts if it is defined, evaluated and justified (help channel, 9/28). Ours is the prompted router against a keyword baseline.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Help channel (9/28)

**Depends on:** [REQ-0017](#req-0017), [REQ-0020](#req-0020). Comparison needs valid labels and a shared held-out.

**Evidence:** Proven by: router and baseline run on the same held-out cases, plus a system replay, in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: the fixtures mirror the baseline, so the measured difference is zero by construction; a live-model run (decision 10) is needed.

<a id="req-0017"></a>
### REQ-0017 · Valid labels, no leakage

Labels must be trustworthy and the evaluation must not see information from the future or from training. Metrics, thresholds and splits must be justified.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12

**Depends on:** [REQ-0015](#req-0015). Labels come from the pipeline output.

**Evidence:** Proven by: 2024Q4 window with the held-out cut 2025-07-01 enforced in code (`evidence/evaluation/method.md`); leak check 5611/5611 in `evidence/evaluation/2024Q4-v1/summary.json`; dev and held-out splits with no shared ids in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: one written justification of metrics, thresholds and splits, confirmed on real Gold.

<a id="req-0020"></a>
### REQ-0020 · Same held-out for baseline and system

Compare the baseline and the system on exactly the same held-out cases, and make that set resemble the real distribution.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: Evaluation evidence · Kickoff p. 12

**Depends on:** [REQ-0017](#req-0017). Held-out built on valid labels.

**Evidence:** Proven by: the same 35 team-written cases for both models and the loop in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json); held-out measured once.

Missing: a justification that the case mix is realistic, or a declared limitation.

<a id="req-0022"></a>
### REQ-0022 · Metrics with n, mix and variability

Every reported metric states how many cases it covers, their mix, the versions used and how much it varies between runs, and failures are included rather than hidden.

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 5; Evaluation evidence

**Depends on:** [REQ-0020](#req-0020), [REQ-0055](#req-0055). Reports the held-out metrics with n and failures.

**Evidence:** Proven by: n, mix, versions and failures per metric in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: run-to-run variability, on the final run.

<a id="req-0055"></a>
### REQ-0055 · Mandatory outcome metrics

Report the brief's outcome metrics: safe automated resolution (plus the share attempted), containment, escalation quality (missed and unnecessary transfers), unsafe outcomes with counts and denominators, p50/p95 latency, and cost per attempted case and per successful resolution ("not defined" if there are none).

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis, ml

**Source:** Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12

**Depends on:** [REQ-0020](#req-0020), [REQ-0025](#req-0025). Metrics on the held-out, latency and cost from the logs.

**Evidence:** Proven by: the full set with denominators in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json); the router reports tokens and cost per turn (`tests/test_ai_router.py`).

Missing: the final [metrics](../build/metrics.md) report on the final run.

<a id="req-0053"></a>
### REQ-0053 · Sizing and its limits

How many disputes per day appear in the data, what capacity the prototype is designed for, and what changes at real volume (help channel, 9/28).

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Help channel (9/28)

**Depends on:** [REQ-0014](#req-0014). Sizing uses the dispute volumes from the analysis.

**Evidence:** Missing: the sizing section.

<a id="req-0057"></a>
### REQ-0057 · Business outcomes and ROI

The intended customer and business outcomes, with cost-per-resolution ROI against the baseline. Projected savings are labeled as projections.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0055](#req-0055). ROI uses cost per resolution.

**Evidence:** Proven by: cost per attempted case and per resolution measured in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json) ("not defined" without resolutions).

Missing: the ROI write-up, labeled as a projection.

<a id="req-0031"></a>
### REQ-0031 · Approved data, labeled by origin

Use only organizer-approved data and label every input as real, de-identified, synthetic or team-generated. The organizer's dataset is fully synthetic (dataset summary: "no real customer information is included").

**Priority:** P0 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Data and execution boundaries

**Evidence:** Missing: the source inventory.

<a id="req-0054"></a>
### REQ-0054 · Justified external data

External data is allowed only if justified: source, license, why it is needed, no personal data, and labeled as external.

**Priority:** P1 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data, ml

**Source:** Help channel (9/28)

**Depends on:** [REQ-0031](#req-0031). Same source inventory.

**Evidence:** Missing: none is used; declare it in the source inventory (REQ-0031).

<a id="req-0018"></a>
### REQ-0018 · Real incremental processing

Show the pipeline updates correctly when data arrives late, is duplicated or changes schema. The data is static, so the brief accepts a clearly labeled test fixture as proof.

**Priority:** P0 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Architecture freedom · Dataset summary

**Depends on:** [REQ-0015](#req-0015). Incremental processing extends the pipeline.

**Evidence:** Missing: the labeled fixture and its test.

<a id="req-0019"></a>
### REQ-0019 · Experiment tracking

Record which model, prompt version, parameters and metrics produced each result, so any run can be traced and repeated.

**Priority:** P1 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Kickoff p. 20

**Depends on:** [REQ-0016](#req-0016). Tracks the learned component's versions.

**Evidence:** Proven by: router `describe` plus tokens and cost on the `understand` record (`tests/test_ai_router.py`); model, route, prompt and label provenance per run in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: the live model's parameters, once decision 10 lands.

<a id="req-0024"></a>
### REQ-0024 · Breakdown by language, country and segment

Compare outcomes by language, country and authorized customer segment (the `segment` column of `customers`: Premium, Plus, Basic, Student), investigate disparities and state small-sample limits. Offline results, simulations and projections are labeled separately.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0012](#req-0012), [REQ-0022](#req-0022). Breakdown of the reported metrics by language and country.

**Evidence:** Proven by: metrics by locale and country with small-sample limits in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json), labeled as offline simulation.

Missing: the segment breakdown and the disparity analysis.

<a id="req-0050"></a>
### REQ-0050 · Monitoring by country

Monitor latency, failures, escalations and complaints per country.

**Priority:** P1 · **Status:** Pending · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring)

**Depends on:** [REQ-0024](#req-0024), [REQ-0025](#req-0025). Country monitoring reads the logs and the breakdown.

**Evidence:** Missing: the report by country from the logs.

<a id="req-0023"></a>
### REQ-0023 · Validated LLM judge, if used

Only applies if a model judges the answers: its rubric must be documented and checked on a sample against human or deterministic judgments.

**Priority:** P2 · **Status:** Pending · **Criterion:** Machine Learning · **Area:** ml · **Flow:** If applicable

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0016](#req-0016). Only applies to an LLM component being judged.

**Evidence:** Not used so far: answers are judged by deterministic checks. Close as not applicable if that holds.

## Delivery (E)

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0034](#req-0034) | Clean public repository | P0 | all | [REQ-0031](#req-0031) | In progress |
| [REQ-0035](#req-0035) | Deployed tool link | P0 | ai | [REQ-0027](#req-0027), [REQ-0034](#req-0034) | Pending |
| [REQ-0036](#req-0036) | Presentation, 4 to 6 slides | P0 | all | [REQ-0055](#req-0055), [REQ-0056](#req-0056) | Pending |
| [REQ-0037](#req-0037) | Video pitch | P0 | all | [REQ-0009](#req-0009), [REQ-0010](#req-0010), [REQ-0011](#req-0011), [REQ-0035](#req-0035) | Pending |
| [REQ-0051](#req-0051) | Everything in English | P0 | all | [REQ-0036](#req-0036), [REQ-0037](#req-0037) | Pending |
| [REQ-0013](#req-0013) | Report data and language limits | P0 | analysis | [REQ-0012](#req-0012), [REQ-0024](#req-0024) | Pending |
| [REQ-0030](#req-0030) | Declare what is missing | P0 | all | [REQ-0013](#req-0013), [REQ-0053](#req-0053) | In progress |
| [REQ-0052](#req-0052) | Path to production | P0 | ai, all | [REQ-0025](#req-0025), [REQ-0050](#req-0050) | In progress |

<a id="req-0034"></a>
### REQ-0034 · Clean public repository

The repository is delivered public as `factored-hackathon-2026-sentinel-engine`, with all links sent to `hackathon.admin@factored.ai`, so it must hold no secrets, private records or restricted data.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0031](#req-0031). No restricted data in the public repo.

**Evidence:** Proven by: the current tree has no bucket name or account id.

Missing: a final secrets and data review, and a decision on the bucket id still present in older commits.

<a id="req-0035"></a>
### REQ-0035 · Deployed tool link

A link to the running tool, with usage and spending limits. A minimal deployment is enough; cloud is not mandatory (help channel, 9/28).

**Priority:** P0 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 18 · Help channel (9/28)

**Depends on:** [REQ-0027](#req-0027), [REQ-0034](#req-0034). A public link needs the session and a clean repo.

**Evidence:** Missing: the deployment and its link.

<a id="req-0036"></a>
### REQ-0036 · Presentation, 4 to 6 slides

A short slide deck describing the tool, part of the mandatory submission.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0055](#req-0055), [REQ-0056](#req-0056). Slides present metrics and trade-offs.

**Evidence:** Missing: the slides. [Script](../build/delivery.md#presentation).

<a id="req-0037"></a>
### REQ-0037 · Video pitch

A short, mandatory video (3 minutes at most) that shows the working solution and explains the core architecture decisions.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0009](#req-0009), [REQ-0010](#req-0010), [REQ-0011](#req-0011), [REQ-0035](#req-0035). The video shows the three demo cases on the deployed tool.

**Evidence:** Missing: the video. [Script](../build/delivery.md#video-pitch).

<a id="req-0051"></a>
### REQ-0051 · Everything in English

The README, slides, video script, `docs/` and `team/` are written in English, since the hackathon is judged in English.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Own: [language](../build/delivery.md#language)

**Depends on:** [REQ-0036](#req-0036), [REQ-0037](#req-0037). Language check covers the slides and video script.

**Evidence:** Missing: the [pre-submission check](../build/delivery.md#language).

<a id="req-0013"></a>
### REQ-0013 · Report data and language limits

State openly what the data cannot support: the dataset is synthetic, Spanish only, and covers only Mexico, Colombia and Argentina, so Portuguese and other countries are untested against real material.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** analysis

**Source:** Problem statement: Scope · Kickoff p. 15 · Dataset summary

**Depends on:** [REQ-0012](#req-0012), [REQ-0024](#req-0024). Coverage limits come from the language support and the breakdown.

**Evidence:** Missing: the limitations section.

<a id="req-0030"></a>
### REQ-0030 · Declare what is missing

An honest list of what the prototype lacks before real use: capacity, data, languages, deployment and remaining risks.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 · Help channel (9/28)

**Depends on:** [REQ-0013](#req-0013), [REQ-0053](#req-0053). Gathers the data, language and capacity limits.

**Evidence:** Missing: the limitations section, which gathers REQ-0013 and REQ-0053.

<a id="req-0052"></a>
### REQ-0052 · Path to production

A credible account of how the prototype would be deployed, scaled, monitored and secured, and what changes from the prototype.

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering / Rationale · **Area:** ai, all

**Source:** Help channel (9/28) · Kickoff p. 15

**Depends on:** [REQ-0025](#req-0025), [REQ-0050](#req-0050). Path to production includes monitoring.

**Evidence:** Proven by: the [path to production](../architecture/specification.md#path-to-production).

Missing: monitoring (REQ-0050) and handoff delivery (decision 28).

## Dependencies

A requirement depends on another when it cannot be met, or its evidence cannot be produced, until the other one is met. Each requirement lists its direct dependencies in its table row and, with the reason, in its card. Update them when a requirement is added or its evidence changes.

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
