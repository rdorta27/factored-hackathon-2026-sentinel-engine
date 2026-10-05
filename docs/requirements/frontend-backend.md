---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Requirements: Frontend and backend

This page covers what the customer and the advisor experience. It also covers the service behind it: conversation, verified answers, tools, policy and handoff. The [requirements index](requirements.md) holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0001](#req-0001) | Keep conversation context | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0002](#req-0002) | Clarify or abstain | P0 | ai | [REQ-0001](#req-0001), [REQ-0003](#req-0003) | Done |
| [REQ-0003](#req-0003) | Answer only from verified records | P0 | ai | [REQ-0015](data-ml.md#req-0015), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0004](#req-0004) | Use tools safely, simulated actions only | P0 | ai | [REQ-0005](non-functional.md#req-0005), [REQ-0007](non-functional.md#req-0007), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0006](#req-0006) | Decide answer, confirm or escalate | P0 | ai | [REQ-0007](non-functional.md#req-0007), [REQ-0033](#req-0033) | Done |
| [REQ-0008](#req-0008) | Structured handoff package | P0 | ai | [REQ-0003](#req-0003), [REQ-0029](non-functional.md#req-0029), [REQ-0047](non-functional.md#req-0047) | Done |
| [REQ-0009](#req-0009) | Demo: normal case | P0 | ai | [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012) | Done |
| [REQ-0010](#req-0010) | Demo: ambiguous or unsupported case | P0 | ai | [REQ-0002](#req-0002) | Done |
| [REQ-0011](#req-0011) | Demo: case requiring a human | P0 | ai | [REQ-0008](#req-0008), [REQ-0040](#req-0040) | Done |
| [REQ-0012](#req-0012) | Works in Spanish and Portuguese | P0 | ai, ml | [REQ-0001](#req-0001) | Done |
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

The system remembers what the customer said earlier in the conversation: the charge under discussion, the pending confirmation and the language. The customer never has to repeat it. The brief lists this first among the minimum behaviors of a functioning AI system.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0027](non-functional.md#req-0027). The system keeps the context for each authenticated session.

**Evidence:** Proven by:

- The conversation state of each session (turns, candidates, pending confirmation, language). It is stored in SQLite and restored after a restart (`tests/test_state_sqlite.py::test_session_conversation_and_case_survive_a_restart`).
- The history of each turn, carried in the handoff (`tests/test_handoff_package.py`).
- The router context behind `ModelPort` (`tests/test_ai_router.py`).
- The handoff reference and reason. They belong to the case. A later request about another charge continues the flow, and a filed reason does not change. A correction with the box open grounds the new charge (`tests/test_flow_fixes.py`; manual test replay points 1 and 3 in [`team/chat-manual-tests.md`](../../team/chat-manual-tests.md)).

<a id="req-0002"></a>
### REQ-0002 · Clarify or abstain

When a request is ambiguous (several charges match), the system asks a question. It does not guess. When a request is out of scope, the system says so and offers a person. It never acts on a guess. This is the "ambiguous or unsupported" demo case.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope; What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0001](#req-0001), [REQ-0003](#req-0003). A clarification needs the conversation so far and the verified candidates.

**Evidence:** Proven by:

- `clarification` replies with ranked candidates, and the out-of-scope handoff (`tests/test_contract.py::test_normal_case_variants_match_the_contract`).
- Adversarial group E in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json).
- Ambiguous cases replayed in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

<a id="req-0003"></a>
### REQ-0003 · Answer only from verified records

Each fact in a reply (amount, merchant, date, case number) comes from the records of the customer. It never comes from the model. If the record does not exist, the system says so. It does not invent the record.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 13

**Depends on:** [REQ-0015](data-ml.md#req-0015), [REQ-0032](non-functional.md#req-0032). The verified facts come from Gold through the tool contracts.

**Evidence:** Proven by:

- A check of each amount and merchant in a reply against the Gold rows of the session customer (`tests/test_facts_grounding.py`, mutation-checked).
- The canary `test_rendered_facts_change_when_gold_changes`.
- A case number that the system shows only after it reads the number back (`tests/test_contract.py`).

<a id="req-0004"></a>
### REQ-0004 · Use tools safely, simulated actions only

The system acts only through tools that are bound to the logged-in customer. It asks for confirmation before each write. It never moves money. Each action is simulated and has a label that says so.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2; Data and execution boundaries · Kickoff p. 11

**Depends on:** [REQ-0005](non-functional.md#req-0005), [REQ-0007](non-functional.md#req-0007), [REQ-0032](non-functional.md#req-0032). Safe tool use needs read-back, permissions in code and documented mock tools.

**Evidence:** Proven by:

- Tools bound to the session.
- Writes only after the confirm box. The writes are idempotent and the system reads them back.
- `source=mock` and `noFundsHeld` on each confirmation.
- No write path that skips the confirmation (`tests/test_disputes_api.py`, adversarial D6 in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json)).

<a id="req-0006"></a>
### REQ-0006 · Decide answer, confirm or escalate

Written rules say what the system answers alone. They say which actions need the confirmation of the customer. They say when the system must hand over to a person. The brief calls this controlled automation.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11

**Depends on:** [REQ-0007](non-functional.md#req-0007), [REQ-0033](#req-0033). Policy in code makes the split between answer, confirm and escalate.

**Evidence:** Proven by:

- The [conversation rules](../build/conversation.md), the policy engine and the confirm box.
- A handoff when the customer insists on a person, when a write is not verified, when the request is out of scope and when the charge is unknown.
- Rules for suspected fraud (`fraud.claim`, `fraud.score`) and for a high amount (`amount.high`), for each account country and currency ([010](../build/decisions/010-fraud-handoff-rule.md), [011](../build/decisions/011-high-amount-threshold.md)). The values come from `evidence/evaluation/2024Q4-v2/summary.json`. One demo charge exists for each rule (`tests/test_not_mine_claim.py`, `tests/test_policy_files.py`). The rules are replayed in `evidence/evaluation-runs/2024Q4-eval-v6/summary.json`.
- A status question about a dispute. The system answers it from the case store before the model. A correction replaces the open box (`tests/test_flow_fixes.py`; manual test replay points 2 and 3).

Two rules stay off or empty: Mexican MXN has no threshold, because the data has no MXN accounts. The staleness rule (decision 27) stays off.

<a id="req-0008"></a>
### REQ-0008 · Structured handoff package

When the system escalates, the advisor receives a structured JSON package. It holds the request, the verified facts, the actions attempted, the evidence and the open questions. It does not hold the raw transcript.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3 · Kickoff p. 11, 14

**Depends on:** [REQ-0003](#req-0003), [REQ-0029](non-functional.md#req-0029), [REQ-0047](non-functional.md#req-0047). The package carries verified facts, rule-based evidence and no PII.

**Evidence:** Proven by:

- The `handoff` reply. It carries the request, a deterministic summary, an entry for each turn, the verified facts, each action attempted (failed actions too), the evidence, the open questions, the language and the country. It has no `customer_id` and no raw text.
- A filed case. The system files the handoff as an escalated case. The advisor reads it at `GET /api/v1/handoffs` (`tests/test_handoff_package.py`, `tests/test_handoffs_api.py`).
- One ticket for each conversation. Later handoff replies reuse its reference (`test_a_conversation_files_one_handoff_ticket`).

<a id="req-0009"></a>
### REQ-0009 · Demo: normal case

This is the first of the three mandatory demo cases. A customer asks about a charge. The system resolves it from start to end according to policy. Here, it opens a verified dispute.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0003](#req-0003), [REQ-0004](#req-0004), [REQ-0006](#req-0006), [REQ-0012](#req-0012). The normal case uses verified data, safe tools and policy, in both languages.

**Evidence:** Proven by:

- The confirm box leads to a verified `case_confirmation` (`tests/test_contract.py`, `tests/test_facts_grounding.py`).
- The normal case in es-MX, es-CO, es-AR and pt-BR. It confirms Cafe Central 320 MXN and returns a case number only after the read-back (`tests/test_demo_pt_br.py`).
- The resolution run [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json). It resolves the eligible situations with a verified case number.
- A run on real Gold. The app reads the view with no PII, and health reports `duckdb`. The normal, ambiguous and handoff cases ran locally in es-419 and pt-BR ([MT-09](../../team/chat-manual-tests.md)).

Missing: nothing for this requirement. The recording is REQ-0037.

<a id="req-0010"></a>
### REQ-0010 · Demo: ambiguous or unsupported case

This is the second mandatory demo case. The system cannot resolve the request as stated. It clarifies or abstains and does not act.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0002](#req-0002). The demo shows the clarify-or-abstain behavior.

**Evidence:** Proven by tests and a run. An ambiguous charge produces a `clarification` with candidates. An out-of-scope request produces a handoff. Nothing opens (`tests/adversarial/test_e_ambiguity.py`, [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json)).

Missing: the video shows it (REQ-0037).

<a id="req-0011"></a>
### REQ-0011 · Demo: case requiring a human

This is the third mandatory demo case. The system must not handle the request alone. It escalates with the handoff package.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Scope · Kickoff p. 11

**Depends on:** [REQ-0008](#req-0008), [REQ-0040](#req-0040). The demo shows the handoff and the request for a person.

**Evidence:** Proven by tests. When the customer insists on a person, or a write is not verified, the system produces a `handoff` with its package. The system files it as a ticket that the advisor reads (`tests/test_handoffs_api.py`, `tests/test_handoff_package.py`).

Missing: the video shows it (REQ-0037).

<a id="req-0012"></a>
### REQ-0012 · Works in Spanish and Portuguese

The system must serve customers in Spanish and in Portuguese (brief: Scope; kickoff p. 10). The data has no Portuguese. The dataset is in Spanish only and covers MX, CO and AR. For this reason, the system must work in Portuguese without data to learn from. The team generates any Portuguese test material and labels it as such.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / ML · **Area:** ai, ml

**Source:** Problem statement: Scope · Kickoff p. 10 · Dataset summary

**Depends on:** [REQ-0001](#req-0001). The system detects the language and keeps it in the conversation state.

**Evidence:** Proven by:

- Spanish (es-419) on the whole demo path.
- Language detection in the router. It includes pt-BR (`tests/test_ai_router.py`).
- Four variants for each of the three demo cases: es-MX, es-CO, es-AR and pt-BR. They run on the keyword baseline (`tests/test_demo_pt_br.py`, [`eval/demo/pt-br.jsonl`](../../sentinel-ai-core/eval/demo/pt-br.jsonl)). The account stays with the charge. The variant is the wording.

[017](../build/decisions/017-portuguese.md) decides how the system serves a Portuguese-speaking customer and how the team reviews pt-BR cases. An MX, CO or AR account is answered in pt-BR. The team checks the cases through a Spanish back-translation.

- DeepSeek V4.1 Flash back-translated the demo pt-BR lines. It is a different model from the writer. [`eval/review/demo-pt-br.md`](../../sentinel-ai-core/eval/review/demo-pt-br.md) records it. This follows the isolated-model method of [018](../build/decisions/018-evaluation-acceptance.md).
- A Colombian teammate accepted the three es-CO lines.
- The same model found no drift on es-MX and es-AR. Nobody on the team speaks those varieties.

Pix is understood as a word and hands off, because the account has no Pix (`tests/test_demo_pt_br.py`). `extrato` and `fatura` are the statement words inside sealed charge inquiries. For this reason, the system does not mark them out of scope. A bare request shows the charges of the account.

A 2% replay used the development side of the 70/30 time split (held-out cut 2025-07-01): 280 of 14023 development openings, seed 20261002. The result is in [`evidence/transcript-chats/20261002T144836Z/summary.json`](../../evidence/transcript-chats/20261002T144836Z/summary.json): 280 handoffs, 2 distinct prefixes and 0 held-out rows on disk. The team wrote no customer text into the repository. The text is templated Spanish. It is not customer language. [REQ-0013](delivery.md#req-0013) reports that limit.

Missing: nothing. The video is [REQ-0037](delivery.md#req-0037). Serving the measured router is [REQ-0016](data-ml.md#req-0016).

<a id="req-0033"></a>
### REQ-0033 · Policy decides, the LLM converses

The model talks to the customer. It never approves anything and never invents rules. Policy code makes the decisions. The brief separates risk and eligibility. That separation is specific to credit. It does not apply to disputes.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / ML · **Area:** ai, ml

**Source:** Problem statement: Data and execution boundaries; What your solution should demonstrate 3

**Depends on:** [REQ-0048](non-functional.md#req-0048). The requirement applies the decision order.

**Evidence:** Proven by the architecture: only the policy engine decides.

- The system answers the "why?" follow-up from the stored decision. It does not call the model, the lookup tool or the engine.
- Each rule may disclose only its own verified values. The window rule and the status rules explain their own rule. The safety rules return one fixed sentence. It names no threshold, no score and not the word fraud.
- No decision invents a rule (`tests/test_explanation.py`, `tests/test_policy_gate.py`, `tests/test_contract.py::test_why_followup_returns_a_strict_explanation`).
- Probing is measured at `0/42` unsafe ([run](../../evidence/adversarial/20261002T195516Z/summary.json)).
- The locale texts hold no written number ([`tests/test_policy_texts.py`](../../sentinel-ai-core/tests/test_policy_texts.py)).

<a id="req-0038"></a>
### REQ-0038 · Simple frontend

Give a simple way to use the system, such as a chat page. A dashboard is not required. The team chose not to build one.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 20

**Depends on:** [REQ-0027](non-functional.md#req-0027). The page runs on the test session.

**Evidence:** Proven by:

- **One page.** The page is at `/ui/` and the same process serves it. It holds the customer chat (confirm box, chips, transactions panel, handoff card) and the read-only advisor view (`tests/test_ui.py`, `tests/test_contract.py::test_served_app_is_the_full_app`).
- **Transactions panel.** It disables the charges that are not eligible and shows why. A reply that is not 2xx shows as an error bubble. It does not show as a bot answer. The team checked this on 10/02 in headless Chromium against the running app: 4 enabled, 3 disabled and a 429 bubble. See [009](../build/decisions/009-demo-ui-and-advisor-view.md).
- **Product interface.** The demo entry, the "Cómo lo resolví" panel, and the advisor list and detail. Four screens exist in es-MX and pt-BR, at desktop and phone width, under [`docs/build/screenshots/ui-product/`](../build/screenshots/ui-product/). The script `scripts/capture_ui_product.py` regenerates them. The notes are in [`team/chat-manual-tests.md`](../../team/chat-manual-tests.md#mt-09).
- **Bank interface (change `bank-ui`).** It adds a bank shell with the masked product and the data date, the charge states from `case_state`, the "Mis reclamos" panel, the handoff card, the phone layout with drawers and the white label (`SENTINEL_BRAND_NAME`, `SENTINEL_BRAND_ACCENT`). The tests are `tests/test_transactions.py`, `tests/test_ui.py`, `tests/test_brand_config.py` and `tests/test_branding.py`. It adds the screens `chat-handoff` and `chat-brand`. The review notes are in [`team/chat-manual-tests.md`](../../team/chat-manual-tests.md#mt-10).

<a id="req-0040"></a>
### REQ-0040 · Request for a person

When the customer asks for a person, the system makes one offer to help. If the customer insists, the system escalates at once.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#when-the-customer-asks-to-speak-to-a-person)

**Depends on:** [REQ-0006](#req-0006). A request for a person is one of the escalation rules.

**Evidence:** Proven by:

- One offer, then a handoff (`tests/test_person_asks.py::test_first_ask_offers_and_second_hands_off_without_classify`).
- The same rule with the confirm box open, in es-419 and pt-BR and for the three countries. No case opens. A second ask escalates, also after other messages (`tests/test_person_while_confirming.py`).
- The agent control (`tests/test_ui.py::test_agent_control_is_two_step_and_session_is_not_stored`).

The rule for a request for a person is in one helper, `app/orchestrator/step.py::_person_request`. Both paths use it: a plain message, and a message that arrives while the confirm box is open. An escalation clears the pending confirmation. A case cannot open while an advisor takes over. The system logs the model call that it makes while the box is open like any other understand step, so its cost counts.

<a id="req-0041"></a>
### REQ-0041 · Original currency, customer's language

The system shows amounts in the original currency of the transaction. The language follows the customer. The currency follows the account.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#language) · Dataset summary (local currency and USD)

**Depends on:** [REQ-0003](#req-0003). The currency is a verified fact of the transaction.

**Evidence:** Proven by:

- The COP and ARS isolation tests (`test_cop_customer_sees_only_cop_charges`, `test_ars_customer_sees_only_ars_charges`).
- A Portuguese conversation that keeps the currency of the charge (`tests/test_facts_grounding.py`).

<a id="req-0042"></a>
### REQ-0042 · Minimum-effort dispute opening

Show the customer their candidate charges to pick from. Do not ask the customer to type amounts or dates.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai · **Flow:** Disputes

**Source:** Own: [conversation](../build/conversation.md#when-opening-a-dispute)

**Depends on:** [REQ-0003](#req-0003), [REQ-0038](#req-0038). The candidates are verified charges that the page shows.

**Evidence:** Proven by tests. A clarification chip, or a tap on the transactions panel, selects exactly one charge. Nothing opens (`tests/test_chat.py`, `tests/test_contract.py`).

<a id="req-0043"></a>
### REQ-0043 · Check charge status first

Before the system opens a dispute, it checks whether the charge is pending, reversed or declined. It then explains. It does not dispute.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai · **Flow:** Disputes, accounts

**Source:** Own: [conversation](../build/conversation.md#when-opening-a-dispute)

**Depends on:** [REQ-0003](#req-0003), [REQ-0015](data-ml.md#req-0015). The charge status is a verified Gold field.

**Evidence:** Proven by:

- The system explains Pending, Reversed and Declined charges and never disputes them. The raw status `Refunded` maps to Reversed (`tests/test_transactions.py`, `tests/test_disputes_api.py::test_preview_runs_the_policy`).
- The system reports an open dispute before the box. A status question never opens a case (`tests/test_flow_fixes.py`; manual test replay points 2 and 5).

<a id="req-0044"></a>
### REQ-0044 · Neutral Spanish with local terms

Replies use neutral Latin American Spanish. They explain local acronyms. The system understands terms from the other countries.

**Priority:** P1 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#language)

**Depends on:** [REQ-0012](#req-0012). The requirement extends the Spanish support.

**Evidence:** Missing: the glossary applied in replies, and a case with a term from another country.

<a id="req-0045"></a>
### REQ-0045 · App-error context

If the customer recently had an error in the app, offer it as a question for context. It is auxiliary. It is not a flow of its own.

**Priority:** P2 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [conversation](../build/conversation.md#app-context)

**Depends on:** [REQ-0001](#req-0001). The system offers the app-error context inside the conversation.

**Evidence:** Missing: not started.

<a id="req-0046"></a>
### REQ-0046 · Handoff routing (simulated)

Route the handoff to an advisor with the right language and specialty. The routing is simulated.

**Priority:** P2 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Own: [AI](../build/areas/ai.md#simulated-routing)

**Depends on:** [REQ-0008](#req-0008), [REQ-0012](#req-0012). The requirement routes the package by language.

**Evidence:** Missing: not started.
