## MODIFIED Requirements

### Requirement: System runner replays the loop and reads the logs

The harness SHALL replay each case against `POST /api/v1/chat` with a test session,
inject the declared faults (Gold unavailable, expired session, tool failure), and
recover the turn's records by `trace_id`. When a case declares the charge to select
and asks for confirmation, the harness SHALL send the selection and then the
confirmation as separate turns, and SHALL stop at the first reply that is not a
`confirm_box`. A case SHALL count as resolved only when the last reply is a
`case_confirmation`. The harness SHALL NOT confirm a case that does not ask for it.
Traces to REQ-0025 (P1, In progress), REQ-0021 (P0, Done) and REQ-0055 (P0, In progress).

#### Scenario: A case is replayed end to end

- **WHEN** a case is run through the system
- **THEN** the turn completes and its outcome is compared with the expected label

#### Scenario: An injected fault is handled and recorded

- **WHEN** a declared fault is injected
- **THEN** the turn degrades safely and the fault appears in the records

#### Scenario: Records are read by trace id

- **WHEN** a turn finishes
- **THEN** the harness reads every record of that turn by its `trace_id`

#### Scenario: A confirmed case ends with a case number

- **WHEN** a case selects an eligible charge and asks for confirmation
- **THEN** the harness sends the confirmation turn and the case ends as `case_confirmation` with a verified case number

#### Scenario: A refused charge is not confirmed

- **WHEN** the selection of a charge ends in a refusal or a handoff
- **THEN** the harness sends no confirmation turn and the case ends with that outcome

#### Scenario: Single-turn cases are unchanged

- **WHEN** a case declares no charge to select
- **THEN** the harness sends one turn as before
