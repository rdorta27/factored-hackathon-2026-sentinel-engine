# Requirements: Frontend and backend

What the customer and the advisor experience, and the service behind it: conversation, verified answers, tools, policy and handoff. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0001](#req-0001) | Keep conversation context | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0002](#req-0002) | Clarify or abstain | P0 | ai | [REQ-0001](#req-0001), [REQ-0003](#req-0003) | Done |
| [REQ-0003](#req-0003) | Answer only from verified records | P0 | ai | [REQ-0015](data-ml.md#req-0015), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0004](#req-0004) | Use tools safely, simulated actions only | P0 | ai | [REQ-0005](non-functional.md#req-0005), [REQ-0007](non-functional.md#req-0007), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0006](#req-0006) | Decide answer, confirm or escalate | P0 | ai | [REQ-0007](non-functional.md#req-0007), [REQ-0033](#req-0033) | Done |
| [REQ-0008](#req-0008) | Structured handoff package | P0 | ai | [REQ-0003](#req-0003), [REQ-0029](non-functional.md#req-0029), [REQ-0047](non-functional.md#req-0047) | Done |
| [REQ-0009](#req-0009) | Demo: normal case | P0 | ai | [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012) | In progress |
| [REQ-0010](#req-0010) | Demo: ambiguous or unsupported case | P0 | ai | [REQ-0002](#req-0002) | Done |
| [REQ-0011](#req-0011) | Demo: case requiring a human | P0 | ai | [REQ-0008](#req-0008), [REQ-0040](#req-0040) | Done |
| [REQ-0012](#req-0012) | Works in Spanish and Portuguese | P0 | ai, ml | [REQ-0001](#req-0001) | In progress |
| [REQ-0033](#req-0033) | Policy decides, the LLM converses | P0 | ai, ml | [REQ-0048](non-functional.md#req-0048) | Done |
| [REQ-0038](#req-0038) | Simple frontend | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0040](#req-0040) | Request for a person | P0 | ai | [REQ-0006](#req-0006) | Done |
| [REQ-0041](#req-0041) | Original currency, customer's language | P0 | ai | [REQ-0003](#req-0003) | Done |
| [REQ-0042](#req-0042) | Minimum-effort dispute opening | P1 | ai | [REQ-0003](#req-0003), [REQ-0038](#req-0038) | Done |
| [REQ-0043](#req-0043) | Check charge status first | P1 | ai | [REQ-0003](#req-0003), [REQ-0015](data-ml.md#req-0015) | Done |
| [REQ-0044](#req-0044) | Neutral Spanish with local terms | P1 | ai | [REQ-0012](#req-0012) | Pending |
| [REQ-0045](#req-0045) | App-error context | P2 | ai | [REQ-0001](#req-0001) | Pending |
| [REQ-0046](#req-0046) | Handoff routing (simulated) | P2 | ai | [REQ-0008](#req-0008), [REQ-0012](#req-0012) | Pending |

<a id="req-0001"></a>
### REQ-0001 · Keep conversation context

The system remembers what was said earlier in the conversation (the charge under discussion, the pending confirmation, the language) so the customer never has to repeat it. The brief lists it first among the minimum behaviors of a functioning AI system.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0027](non-functional.md#req-0027). Context is kept per authenticated session.

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

**Depends on:** [REQ-0015](data-ml.md#req-0015), [REQ-0032](non-functional.md#req-0032). Verified facts come from Gold through the tool contracts.

**Evidence:** Proven by: every amount and merchant in a reply is checked against the session customer's Gold rows (`tests/test_facts_grounding.py`, mutation-checked); canary `test_rendered_facts_change_when_gold_changes`; a case number is shown only after it is read back (`tests/test_contract.py`).

<a id="req-0004"></a>
### REQ-0004 · Use tools safely, simulated actions only

The system acts only through tools bound to the logged-in customer, asks for confirmation before any write, and never moves money: every action is simulated and labeled as such.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2; Data and execution boundaries · Kickoff p. 11

**Depends on:** [REQ-0005](non-functional.md#req-0005), [REQ-0007](non-functional.md#req-0007), [REQ-0032](non-functional.md#req-0032). Safe tool use needs read-back, permissions in code and documented mock tools.

**Evidence:** Proven by: session-bound tools; writes only after the confirm box, idempotent and read back; `source=mock` and `noFundsHeld` on every confirmation; no write path skips confirmation (`tests/test_disputes_api.py`, adversarial D6 in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json)).

<a id="req-0006"></a>
### REQ-0006 · Decide answer, confirm or escalate

Written rules say what the system answers alone, which actions need the customer's confirmation, and when it must hand over to a person. The brief calls this controlled automation.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11

**Depends on:** [REQ-0007](non-functional.md#req-0007), [REQ-0033](#req-0033). The answer/confirm/escalate split is policy in code.

**Evidence:** Proven by: the [conversation rules](../build/conversation.md), the policy engine and the confirm box; handoff on person insist, unverified write, out of scope and unknown charge; suspected fraud (`fraud.claim`, `fraud.score`) and high amount (`amount.high`) per account country and currency ([010](../build/decisions/010-fraud-handoff-rule.md), [011](../build/decisions/011-high-amount-threshold.md)), with values from `evidence/evaluation/2024Q4-v2/summary.json` and one demo charge per rule (`tests/test_not_mine_claim.py`, `tests/test_policy_files.py`); replayed in `evidence/evaluation-runs/2024Q4-eval-v6/summary.json`. Mexican MXN has no threshold (no MXN accounts in the data); staleness (decision 27) stays off.

<a id="req-0008"></a>
### REQ-0008 · Structured handoff package

When the system escalates, the advisor receives a structured JSON package with the request, the verified facts, the actions attempted, the evidence and the open questions, not the raw transcript.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14

**Depends on:** [REQ-0003](#req-0003), [REQ-0029](non-functional.md#req-0029), [REQ-0047](non-functional.md#req-0047). The package carries verified facts, rule-based evidence and no PII.

**Evidence:** Proven by: the `handoff` reply carries request, a deterministic summary, per-turn entries, verified facts, every action attempted (failed ones included), evidence, open questions, language and country, with no `customer_id` and no raw text; it is filed as an escalated case the advisor reads at `GET /api/v1/handoffs` (`tests/test_handoff_package.py`, `tests/test_handoffs_api.py`); a conversation files one ticket, and later handoff replies reuse its reference (`test_a_conversation_files_one_handoff_ticket`).

<a id="req-0009"></a>
### REQ-0009 · Demo: normal case

The first of the three mandatory demo cases: a customer asks about a charge and the system resolves it end to end according to policy (here, opening a verified dispute).

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012). The normal case uses verified data, safe tools and policy, in both languages.

**Evidence:** Proven by: the confirm box leads to a verified `case_confirmation` (`tests/test_contract.py`, `tests/test_facts_grounding.py`); replayed in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: the same case in Portuguese (REQ-0012) and the video (REQ-0037).

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

How a Portuguese-speaking customer is served and how pt-BR cases are reviewed is decided ([017](../build/decisions/017-portuguese.md)): an MX, CO or AR account answered in pt-BR, with cases checked through Spanish back-translation.

Missing: the pt-BR twins of the key cases, written and checked that way. Planned in [`llm-evaluation`](../../openspec/changes/llm-evaluation/proposal.md): every base case in es-MX, es-CO, es-AR and pt-BR, judged per variant by D6 in [018](../build/decisions/018-evaluation-acceptance.md).

<a id="req-0033"></a>
### REQ-0033 · Policy decides, the LLM converses

The model talks to the customer but never approves anything or invents rules; decisions come from policy code. The brief's separation of risk and eligibility is specific to credit and does not apply to disputes.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / ML · **Area:** ai, ml

**Source:** Problem statement: Data and execution boundaries; What your solution should demonstrate 3

**Depends on:** [REQ-0048](non-functional.md#req-0048). Applies the decision order.

**Evidence:** Proven by: the architecture, where only the policy engine decides.

<a id="req-0038"></a>
### REQ-0038 · Simple frontend

A simple way to use the system, such as a chat page. A dashboard is not required, and we chose not to build one.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 20

**Depends on:** [REQ-0027](non-functional.md#req-0027). The page runs on the test session.

**Evidence:** Proven by: one page at `/ui/` served by the same process with the customer chat (confirm box, chips, transactions panel, handoff card) and the read-only advisor view (`tests/test_ui.py`, `tests/test_contract.py::test_served_app_is_the_full_app`); the transactions panel disables charges that are not eligible and shows why, and a non-2xx reply renders as an error bubble instead of a bot answer (checked on 10/02 in headless Chromium against the running app: 4 enabled, 3 disabled, a 429 bubble); [009](../build/decisions/009-demo-ui-and-advisor-view.md).

<a id="req-0040"></a>
### REQ-0040 · Request for a person

When the customer asks for a person, the system makes one offer to help and, if they insist, escalates at once.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person)

**Depends on:** [REQ-0006](#req-0006). A person request is one of the escalation rules.

**Evidence:** Proven by: one offer, then handoff (`tests/test_person_asks.py::test_first_ask_offers_and_second_hands_off_without_classify`); the same rule with the confirm box open, in es-419 and pt-BR and for the three countries, with no case opened, and a second ask escalating even after other messages (`tests/test_person_while_confirming.py`); the agent control (`tests/test_ui.py::test_agent_control_is_two_step_and_session_is_not_stored`).

The person-request rule lives in one helper, `app/orchestrator/step.py::_person_request`, used by both paths: a plain message and a message arriving while the confirm box is open. Escalation clears the pending confirmation, so a case cannot be opened while an advisor is taking over. The model call made while the box is open is logged like any other understand step, so its cost counts.

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

**Depends on:** [REQ-0003](#req-0003), [REQ-0015](data-ml.md#req-0015). Charge status is a verified Gold field.

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
