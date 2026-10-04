## ADDED Requirements

### Requirement: One-click demo personas behind the demo flag

When `SENTINEL_DEMO_AUTH=1`, the entry SHALL offer demo personas that sign in with one click as fixture users: a normal case in es-MX, an ambiguous case in pt-BR on the Mexican account, a high-amount case in es-CO and a "not me" case in es-AR. A banner SHALL state that data is simulated and that the test access needs no password. Without the flag, the personas and the one-click route SHALL NOT exist and the user-and-password form SHALL be the only entry. The personas SHALL NOT show customer identifiers. Traces to REQ-0010 (P0, Done), REQ-0011 (P0, Done), REQ-0012 (P0, Done) and REQ-0027 (P0, Done).

#### Scenario: Personas only in demo mode

- **WHEN** the app starts without `SENTINEL_DEMO_AUTH=1`
- **THEN** the one-click route answers 404 and no persona is shown

#### Scenario: A persona opens its case

- **WHEN** the evaluator chooses the high-amount persona
- **THEN** a session for the Colombian fixture customer starts in es-CO under the demo banner

### Requirement: The customer sees how each turn was resolved in plain language

Each chat reply SHALL carry the ordered steps of its turn as translation keys from a closed list (understood the request, looked up the charges, checked the policy, opened and verified a case, did not open a case, handed off to an advisor, refused), and the interface SHALL render them as a "Cómo lo resolví" panel. No step SHALL contain a model name, tool name, rule id, score, threshold or identifier. Traces to REQ-0029 (P1, Done), REQ-0006 (P0, Done) and REQ-0047 (P0, Done).

#### Scenario: A handoff turn is explained without internals

- **WHEN** a high-amount charge is handed off
- **THEN** the panel shows understood, looked up, checked the policy, did not open a case and handed off, and the reply contains no rule id, model or threshold

#### Scenario: No status hints at fraud before the customer acts

- **WHEN** the transaction panel lists a charge whose fraud score is above the threshold
- **THEN** its status label shows the transaction status only

### Requirement: The advisor sees the turn trace

The advisor's ticket detail SHALL show the handoff package and the trace of the turn that filed the ticket: each step with its outcome and latency, the model and prompt version, the cost and the policy version. The trace SHALL be served only to the advisor role and SHALL contain no customer text or identifier. Traces to REQ-0025 (P1, Done), REQ-0008 (P0, Done) and REQ-0007 (P0, Done).

#### Scenario: A customer cannot read a trace

- **WHEN** a customer session requests a ticket trace
- **THEN** the request is refused

#### Scenario: The advisor sees the steps

- **WHEN** the advisor opens a ticket
- **THEN** the detail lists the steps of the escalating turn with outcome and latency

### Requirement: The interface carries the product identity

The interface SHALL show the product mark and the line stating its purpose, load fonts and assets only from `branding/`, use a success color distinct from the accent for verified states, and keep a text label on every status color. Traces to REQ-0038 (P0, Done).

#### Scenario: No external font request

- **WHEN** the page loads
- **THEN** no font or asset is requested from outside the app
