# observability Specification

## Purpose

Gives every conversation turn a structured, PII-free receipt that tracing, monitoring, and the evaluation runner all read, so turn cost, latency, and the deciding rule are measurable instead of assumed.

## Requirements

### Requirement: One record per loop step

Each pass through the charge-inquiry loop SHALL emit one JSON record per step (`understand`, `decide`, `act`, `verify`, `escalate`) carrying `ts`, `trace_id`, `session_ref`, `step`, `tool`, `outcome` (`ok`, `rejected`, `failed`, `timeout`), `attempt` (integer, 1 or higher), `policy_rule` (the deciding rule id, or null when the step evaluated no policy), `latency_ms` (number, 0 or higher), `model`, `route`, `prompt_version` (non-empty strings; mock values while fakes serve), `tokens_in`, `tokens_out` (integers), `cost_usd` (number), `language` (`es-419` or `pt-BR`), and `country` (`MX`, `CO`, or `AR`). Traces to REQ-0025 (P0, In progress) and REQ-0019 (P1, Pending).

#### Scenario: Decide step names its rule

- **WHEN** the policy engine decides a turn
- **THEN** the `decide` record carries the deciding `policy_rule` and the turn explanation cites that rule, never model reasoning

#### Scenario: Tool calls record outcome and latency

- **WHEN** a tool is called during `act` or `verify`
- **THEN** the record carries the tool name, its outcome, the attempt number, and a numeric `latency_ms`

### Requirement: One closing record per turn

Every `POST /chat` turn SHALL emit exactly one closing record with the final outcome and aggregated cost and latency, sharing the turn `trace_id`, including turns that end in error or handoff so failures stay measurable. Traces to REQ-0055 (P0, Pending) and REQ-0025 (P0, In progress).

#### Scenario: Failed turns stay measurable

- **WHEN** a turn ends in an error or an unknown-charge handoff
- **THEN** a closing record with that outcome and numeric aggregates still exists under the turn `trace_id`

### Requirement: Records never carry personal data

No record SHALL contain customer text, `customer_id`, passwords, confirmation tokens, client IPs, or full session tokens. `session_ref` SHALL be a salted hash of the session, never the identifier. Traces to REQ-0047 (P0, In progress) and REQ-0029 (P1, In progress).

#### Scenario: Grep over the log finds no personal data

- **WHEN** a full turn (login, chat, confirmation) completes
- **THEN** none of its JSON lines contain the customer login, the password, the message text, or the confirmation token

### Requirement: Dual sink readable by the runner

Records SHALL append to an in-memory list and to a JSON-lines file whose path is configurable, so the evaluation runner can replay a whole turn by filtering on `trace_id`. Traces to REQ-0025 (P0, In progress) and REQ-0024/REQ-0050 (P1, Pending, language and country breakdown).

#### Scenario: Turn replay from the file

- **WHEN** the runner filters the file by one `trace_id`
- **THEN** it recovers every step record plus the closing record of that turn
