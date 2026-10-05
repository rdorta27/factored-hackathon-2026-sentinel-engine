## ADDED Requirements

### Requirement: Parallel confirmations open one case

N parallel confirmations of the same candidate in one session SHALL open exactly one case. Traces to REQ-0005 (P0, Done) and REQ-0026 (P1, Done).

#### Scenario: Two clicks at the same time

- **WHEN** two confirmations of one candidate arrive at the same time
- **THEN** the case store holds one case and both replies give the same case number

### Requirement: A pending confirmation expires

A pending confirmation SHALL expire five minutes after it is created. A confirmation of an expired box SHALL not write, and the loop SHALL ask again. Traces to REQ-0005 (P0, Done) and REQ-0007 (P0, Done).

#### Scenario: Late confirmation

- **WHEN** the customer confirms a box that is six minutes old
- **THEN** no case opens and the loop shows the candidate again

### Requirement: A strict mode refuses stale or missing Gold

With `SENTINEL_GOLD_REQUIRED` on, the service SHALL refuse to start when Gold is missing or older than the maximum age. With it off, the service SHALL fall back to the labelled mock and SHALL say so in `/health`. Traces to REQ-0039 (P0, Done) and REQ-0052 (P0, In progress).

#### Scenario: Strict mode and missing Gold

- **WHEN** the mode is on and the Gold file is missing
- **THEN** the service stops at startup and names the reason

### Requirement: Audit records form a chain

Each audit record SHALL hold the hash of the previous record, and a check SHALL report a record that was changed or removed. `/health` SHALL show one hash of the files that decide behavior. Traces to REQ-0025 (P1, Done) and REQ-0029 (P1, Done).

#### Scenario: A removed record

- **WHEN** a record is removed from the log
- **THEN** the check names the position where the chain breaks

### Requirement: A daily budget caps model spend

When the model spend of the day reaches `SENTINEL_LLM_DAILY_BUDGET_USD`, the keyword baseline SHALL answer the next turns, and the turn log SHALL record `budget` as the route. Traces to REQ-0026 (P1, Done) and REQ-0055 (P0, Done).

#### Scenario: Budget reached

- **WHEN** the spend of the day is at the budget
- **THEN** the next turn makes no model call and its record has the route `budget`
