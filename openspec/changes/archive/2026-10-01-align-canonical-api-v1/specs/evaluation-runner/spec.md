# Spec Delta

## MODIFIED Requirements

### Requirement: System runner replays the loop and reads the logs

The harness SHALL replay each case against `POST /api/v1/chat` with a test session,
inject the declared faults (Gold unavailable, expired session, tool failure), and
recover the turn's records by `trace_id`. Traces to REQ-0025 (P1, In progress)
and REQ-0021 (P0, Done).

#### Scenario: A case is replayed end to end

- **WHEN** a case is run through the system
- **THEN** the turn completes and its outcome is compared with the expected label

#### Scenario: An injected fault is handled and recorded

- **WHEN** a declared fault is injected
- **THEN** the turn degrades safely and the fault appears in the records

#### Scenario: Records are read by trace id

- **WHEN** a turn finishes
- **THEN** the harness reads every record of that turn by its `trace_id`
