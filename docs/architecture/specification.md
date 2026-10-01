# Architecture Specification

The contracts and rules behind the [System Architecture](system-architecture.md) and the [Demo Architecture](demo-architecture.md). The two architecture pages show the shape; this page specifies how each piece behaves. Requirements are cited as `REQ-####` ([requirements](../requirements/requirements.md)); open decisions as numbers ([pending decisions](../../team/pending-decisions.md)).

## Scope

The entry point is an **account inquiry about charges and transactions**: what a charge is, why it is Declined, Pending or Reversed, and whether it can be disputed. Balances, product details, cards and credit are out of scope; the assistant says so and offers a handoff (REQ-0002). This keeps one coherent workflow with a single read tool ([decision 24](../../team/pending-decisions.md#decided)).

## Orchestrator loop

The loop comes from the hackathon brief: **Understand → Decide → Act → Verify → Escalate** ([flow candidates](../build/flows/01-flow-candidates.md)). Each step has one owner.

| Step | Owner | What happens | Requirements |
|---|---|---|---|
| Understand | LLM | Classifies intent (charge inquiry, dispute, out of scope), extracts the charge the customer refers to, detects the customer's language. Asks a clarifying question or abstains when the request is ambiguous or out of scope. | REQ-0001, REQ-0002, REQ-0012 |
| Decide | Code | Applies the [decision priority](#decision-priority): policy, then the learned component, then the LLM. Decides whether a dispute applies, needs confirmation, or must be escalated. | REQ-0006, REQ-0033, REQ-0048 |
| Act | Code (tools) | Calls a session-bound tool. Only after explicit customer confirmation for state-changing actions. | REQ-0004, REQ-0042, REQ-0043 |
| Verify | Code (tools) | Reads the result back from the store. An action is reported only when the read-back succeeds; a timeout is not success. | REQ-0003, REQ-0005 |
| Escalate | Code (tools) | Builds the JSON handoff when policy requires it, when verification fails after bounded retries, or when the customer insists on a person. | REQ-0008, REQ-0011, REQ-0040 |

## Tool contracts

Four tools. Each is bound to the session's `customer_id`, which the orchestrator injects; the LLM never supplies or sees it ([decision 005](../build/decisions/005-backend.md), REQ-0047). Contracts are documented so that mocks and production backends are interchangeable (REQ-0032).

| Tool | Input (from the LLM or orchestrator) | Output | Guarantees |
|---|---|---|---|
| `lookup_transactions` | Optional filters: date range, merchant hint, amount hint | Candidate charges, each with an opaque candidate id, status (Approved, Declined, Pending, Reversed), amount in the original currency, merchant, date, and the data as-of date | Only the session customer's charges. Never fabricates a charge (REQ-0003, REQ-0041). |
| `open_dispute` | Candidate id, `confirmation_token`, dispute category (from the [learned component](system-architecture.md#learned-component)), customer statement, idempotency key | Dispute id and write status | Validates the mandatory fields for the account's country, from configuration (REQ-0049); a missing field is asked for, not invented. Rejects the call without a valid `confirmation_token` for that candidate and session. One record per idempotency key: a retry with the same key returns the existing case (REQ-0026). |
| `lookup_dispute` | Dispute id | The stored record, or not found | The case number reaches the customer only when this read succeeds (REQ-0005). |
| `handoff` | Reason for escalation | JSON package: request, verified facts, actions taken, evidence, open questions, language, country | No raw transcript, no identifiers beyond what the advisor is authorised to see (REQ-0008, REQ-0046). |

There is no advisor UI. The JSON package is the handoff.

### Confirmation

State-changing actions need an explicit, structured confirmation (REQ-0006). A free-text "yes" interpreted by the LLM is not a confirmation.

1. The orchestrator shows the selected candidate in a confirm box in the chat (`.chat-confirm` in [`branding/chat.css`](../../branding/chat.css)), with amount, currency, merchant and date.
2. The customer presses confirm. The page sends the candidate id back to `POST /api/v1/chat` as a structured field, not as text.
3. The orchestrator issues a single-use `confirmation_token` bound to session, candidate and action, with a short expiry.
4. `open_dispute` accepts only that token. The LLM never sees, creates or forwards it.

## Decision priority

When more than one component could decide, the higher one wins (REQ-0048):

```mermaid
flowchart TD
    req(["Decision request"]) --> policy{"Does a policy<br/>rule apply?"}
    policy -- "escalate" --> handoff["Handoff to advisor"]
    policy -- "allow / deny" --> apply["Apply the rule"]
    policy -- "no rule" --> learned{"Does the learned<br/>component apply?"}
    learned -- "yes" --> classify["Learned component<br/>assigns the dispute category"]
    learned -- "no" --> llm["LLM drafts the reply<br/>and proposes a tool"]
    classify --> llm
    apply --> llm
    handoff --> done(["Outcome"])
    llm --> done

    classDef real fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef stop fill:#fff0f5,stroke:#ff4f8b,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class req,done ext
    class apply,classify,llm real
    class handoff stop
```

1. **Policy in code.** Permissions, confirmations and fixed rules. A policy outcome is final.
2. **Learned component**, when a dispute applies. It assigns the dispute category that `open_dispute` records. It never decides eligibility or overrides a rule.

Policy rules for this flow. Thresholds are country configuration (REQ-0049); the open ones are tracked in [pending decisions](../../team/pending-decisions.md).

| Rule | Signal available at runtime | Outcome |
|---|---|---|
| Charge is Pending or Reversed | `transaction_status` | Explain the status; no dispute (REQ-0043). |
| Charge is Declined | `transaction_status` | Explain; nothing to dispute. |
| Customer asks for a person | Intent | One offer to help, then handoff (REQ-0040). |
| Suspected fraud | Customer states the charge was not theirs, and/or `fraud_score` above a threshold. `is_fraud` is never used: it is a label known after the fact. | Handoff (decision 25, open). |
| High amount | Charge amount above a per-country threshold, in the original currency | Handoff (decision 26, open). |
| Mandatory information missing after clarification | Country field validation | Handoff with open questions. |
3. **LLM.** Wording the reply and proposing the next tool call. The orchestrator validates every proposed call against policy before executing it; the LLM never chooses which customer's data to read.

## Personal data

**PII** (personally identifiable information) is any data that identifies a customer or is sensitive about them: name, national id, account or card numbers, income, credit score, IP address. The rule (REQ-0047) is that the LLM never receives it, and that no restricted data goes to an external model.

The target enforces this with **data minimisation at three boundaries**, all in code:

| Boundary | Control | Status |
|---|---|---|
| Gold → service | The service reads a serving view with only the [data contract](#data-contract) columns. Names, credit score and `is_fraud` stay in the data layer. | Proposed to the data owner; today `gold_dispute_eligible_transactions` also carries customer name and credit score |
| Tools → LLM | Tools return only the fields the reply needs (amount, currency, merchant, date, status, opaque candidate id). `customer_id` is injected by the orchestrator and never returned. | Target contract |
| Logs | No customer text and no `customer_id` in clear; the session is a salted hash. | Target contract |

What the customer types is the remaining gap: if they write their national id in the chat, it reaches the LLM. Masking free text before the LLM (a token vault) and static masking in Silver are **proposed, not built** ([decision 004](../build/decisions/004-pii-lifecycle.md)); the demo states this as a limitation. Rules: [security](../build/security.md).


## Failure handling

Failures degrade to a safe answer or a handoff, never to an unverified claim (REQ-0021, REQ-0026).

| Failure | Behaviour |
|---|---|
| Gold unavailable | Tell the customer the lookup is not available; offer a handoff. Do not guess charges. |
| Gold older than expected | Answer with the as-of date stated ("updated through…"); never claim a more recent state (REQ-0039). The staleness threshold is open (decision 27). |
| Dispute write or read-back fails or times out | Retry with the same idempotency key, bounded. If still unverified, escalate with the attempt recorded in the handoff; do not give a case number. |
| LLM error or timeout | Bounded retry, then a fixed fallback message and a handoff offer. |
| Proposed tool call violates policy | Rejected by the orchestrator and logged. The LLM is asked to reply without it. |
| Session missing or expired | No tool is called; the customer is asked to authenticate again (REQ-0027). |
| Prompt injection in customer text | Has no effect on permissions: tools are session-bound and policy is in code. Covered by failure tests (REQ-0021). |

## Language and locale

- The reply language follows the customer (`es-419` or `pt-BR`); the currency follows the account and amounts are shown in the charge's original currency (REQ-0041).
- Local acronyms and terms are understood and explained ([glossary](../understand/glossary/), REQ-0044).
- Country (MX, CO, AR) is configuration, not code (REQ-0049). The dataset contains no Portuguese text, so `pt-BR` cases are team-generated and labelled as such (REQ-0012, REQ-0013).

## Conversation state

Context is kept per session by the orchestrator, not by the LLM (REQ-0001).

- **Contents:** the last turns (bounded window), candidates shown, pending confirmation, detected language, clarification count.
- **Lifetime:** tied to the session. When the session expires the state is deleted and the next message requires a new session (REQ-0027).
- **What the LLM gets:** the bounded window of turns and the tool results, never the session or candidate internals.

## Policy source

Rules are evaluated in code, in the policy engine (`app/policy/`), which also applies the [decision priority](#decision-priority). Their parameters (status explanations, per-country fields, deadlines and thresholds) live in one versioned configuration file per country (`config/policy/`), not in code and not in prompts (REQ-0007, REQ-0049). Adding a country changes configuration only.

- **Contents:** meaning of each transaction status and whether it is disputable; mandatory dispute fields; filing deadlines; handoff thresholds (decisions 25, 26, 27).
- **Traceability:** each entry has an id. Replies that explain a rule cite it, and the log records it as `policy_rule` (REQ-0029).
- **Labelling:** the dataset ships no bank policy, so the file is a **synthetic policy** written by the team and labelled as such (REQ-0031).

## Data contract

`lookup_transactions` reads one Gold table, `gold_dispute_eligible_transactions`, through a serving view limited to the columns below. The pipeline in `sentinel-data-engine/` owns schema contracts, quality checks, deduplication and lineage (REQ-0015); details in [data](../build/areas/data.md).

- **Columns consumed:** transaction id, customer id (filter only, never returned to the LLM), date, amount, currency, merchant, status, `fraud_score`.
- **Eligibility columns computed in Gold:** `is_disputed`, `days_since_transaction`, `is_eligible_for_dispute` (90-day window). `days_since_transaction` is computed when Gold is built, so it ages between runs; the policy engine recomputes the window from the transaction date at request time and treats the Gold flag as a hint.
- **Not exposed to the service:** customer name, segment, credit score and `is_fraud`, which the current table also carries (see [personal data](#personal-data)).
- **As-of date:** the latest processed `process_date` in Gold, returned with every read (REQ-0039).
- **Update correctness:** a labelled fixture with late arrivals, duplicates and a schema change proves incremental processing (REQ-0018).

## Observability

Every step of every turn emits one structured log record (REQ-0025). The same records feed tracing, monitoring and the [evaluation](#evaluation) metrics; there is no separate instrumentation.

| Field | Purpose |
|---|---|
| `trace_id` | One per turn; joins LLM calls, tool calls and the reply |
| `session_ref` | Salted hash of the session; never the `customer_id` |
| `step` | Loop step: understand, decide, act, verify, escalate |
| `tool`, `outcome`, `attempt` | Tool called, result (ok, rejected, failed, timeout) and retry number |
| `policy_rule` | Id of the rule that decided, from the [policy source](#policy-source) |
| `latency_ms` | Per step and per turn, for p50/p95 |
| `model`, `route`, `prompt_version` | Reproducibility and experiment tracking (REQ-0019) |
| `tokens_in`, `tokens_out`, `cost_usd` | Cost per attempted case and per resolution (REQ-0055) |
| `language`, `country` | Breakdown and monitoring by segment (REQ-0024, REQ-0050) |

Customer text and identifiers are not logged in clear. Explanations of a decision cite the rule, tool result or log record, never the model's reasoning (REQ-0029).

## Evaluation

The system is measured offline on held-out, labelled conversations, with the same harness for the system and the baseline (REQ-0020, REQ-0022, REQ-0055).

- **Cases:** a versioned JSONL file. Each case has language, country, session, customer turns, and expected outcome (resolve, explain, clarify, abstain, escalate), expected category and whether a handoff is required. Text is team-generated in `es-419` and `pt-BR` and labelled as such.
- **Mix:** normal, ambiguous or unsupported, human-required, plus the failure set of REQ-0021: wrong or missing data, expired session, access to another customer's charge, prompt injection, tool failure, multilingual ambiguity.
- **Runner:** replays each case against `POST /api/v1/chat` with a test session and fault injection in the tools, then reads the log records by `trace_id`. Repeated runs measure variability.
- **Baseline:** the same cases with the keyword baseline in place of the learned component.

| Metric (brief) | Computed as |
|---|---|
| Safe automated resolution | In-scope cases with the correct, policy-compliant outcome and no handoff ÷ all in-scope cases; plus the share where automation was attempted |
| Containment | Cases ended without handoff ÷ all cases (reported, not used as success) |
| Escalation quality | Missed and unnecessary handoffs against the expected label; handoff package completeness |
| Unsafe outcomes | Unauthorized disclosure or action, or materially wrong outcome, with count and denominator |
| Operating efficiency | p50/p95 end-to-end latency; cost per attempted case and per safe resolution ("not defined" when there are none) |

Every metric is broken down by language and country with n. Results are frozen in `evidence/` like the flow measurements and labelled as offline simulation, never as production improvement.

## Data retention

REQ-0027. Proposed; confirm with [security](../build/security.md#data).

| Data | Demo | Production (proposed) |
|---|---|---|
| Conversation state | Process memory, deleted on session expiry or restart | Deleted on session expiry |
| Log records | Local files, no customer text | Centralized, 90 days, no customer text |
| Dispute records | Process memory | Kept per the bank's regulatory retention |
| Handoff packages | Response and log | With the dispute record |
| LLM provider | No retention, no training use | Same, contractual |

## Capacity

REQ-0053. Demand in the development window: `disputes.unrecognized_claim` and `accounts.reason_transaccional` in the [flow measurements](../build/flows/02-flow-measurements.md) (per-day figures derived there). The prototype is sized for that order of magnitude.

- **Prototype limit:** one process; throughput bound by the LLM provider's rate limit and usage cap, and dispute state lost on restart. To be measured by the evaluation runner under concurrency.
- **At real volume:** horizontal replicas of the same process (state moved out of the process to the relational store), per-route LLM quotas, and Gold served from Databricks SQL.

## Trade-offs

REQ-0056. Where AI is used and where it is not.

| Axis | Choice | Why |
|---|---|---|
| Autonomy | Low by design: confirmation for every write, handoff on policy triggers | A wrong dispute or a missed fraud case costs more than a transfer |
| Accuracy | Policy and status from code and data; LLM only for language and category | Deterministic where rules exist; the LLM where language is the problem |
| Latency | One LLM call to understand, one to reply; tools are local reads | Keeps p95 bounded; the loop avoids open-ended agent chains |
| Cost | Router sends frequent, simple turns to a cheaper model (decision 10) | Cost per resolution is a reported metric |
| Human oversight | Structured handoff with verified facts and open questions | The advisor starts from evidence, not from a transcript |

## Path to production

REQ-0052. Cloud deployment is not mandatory (REQ-0035). The demo runs the same code; which components it mocks is listed once, in [mocked components](demo-architecture.md#mocked-components). This table lists only what has to change or be decided before operating.

| Area | Work before production |
|---|---|
| Identity | Replace the test session with an identity provider; move secrets to Azure Key Vault |
| Dispute record and conversation state | Choose the relational engine (SQLite and PostgreSQL are candidates) and move both stores out of process memory |
| Gold serving | Decide how the service reads Gold at request time (not decided; see [stack](system-architecture.md#stack-and-deployment)) and deploy the Gold build to Databricks |
| Policy | Replace the synthetic configuration with the bank's approved policy, same format; set thresholds (decisions 25–27) |
| Handoff | Decide how the JSON package reaches advisors: queue, CRM ticket or similar (decision 28); routing by language and specialty is REQ-0046 (P2) |
| Personal data | Serving view without personal columns; masking of free text and of Silver if adopted ([decision 004](../build/decisions/004-pii-lifecycle.md)) |
| Serving | Container Apps with autoscaling (decision 13) |
| LLM | Per-route quotas and a model per route (decision 10) |
| Observability | Centralised logs and traces, alerts by country (REQ-0050) |
| Evaluation | Run the same harness as a release gate |
| Data retention | Confirm the proposed retention periods ([data retention](#data-retention)) |

Deployment cost is tracked separately in [cost](../build/cost.md).
