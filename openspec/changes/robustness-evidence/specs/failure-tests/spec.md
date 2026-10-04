## ADDED Requirements

### Requirement: Tool failures are measured as a rate

A fault-injection run SHALL inject model timeouts, model errors, invalid model JSON, slow Gold, Gold errors and case-store errors. For each fault it SHALL report the outcome, the added latency, and the share of turns that end in a safe reply or a handoff, with counts and denominators. Traces to REQ-0021 (P0, Done) and REQ-0026 (P1, Done).

#### Scenario: Model timeout

- **WHEN** the model times out on every call
- **THEN** the keyword baseline answers each turn and the run counts no unsafe outcome

### Requirement: Parallel confirmations open one case

N parallel confirmations of the same candidate in one session SHALL open exactly one case. Traces to REQ-0005 (P0, Done) and REQ-0026 (P1, Done).

#### Scenario: Two clicks at the same time

- **WHEN** two confirmations of one candidate arrive at the same time
- **THEN** the case store holds one case and both replies give the same case number

### Requirement: A daily budget caps model spend

When the model spend of the day reaches `SENTINEL_LLM_DAILY_BUDGET_USD`, the keyword baseline SHALL answer the next turns, and the turn log SHALL record `budget` as the route. Traces to REQ-0026 (P1, Done) and REQ-0055 (P0, Done).

#### Scenario: Budget reached

- **WHEN** the spend of the day is at the budget
- **THEN** the next turn makes no model call and its record has the route `budget`
