# Spec Delta

## MODIFIED Requirements

### Requirement: Structured response variants

Every chat answer SHALL use exactly one variant: `text`, `clarification`, `case_confirmation`, `handoff`, or `error`. The `error` variant SHALL carry a generic message plus `trace_id`, never internal details. A `clarification` SHALL be able to carry the candidate transactions the customer can choose from. Traces to REQ-0002 (P0, Pending) and REQ-0006 (P0, Pending).

#### Scenario: Ambiguous request asks instead of guessing

- **WHEN** the request does not identify which transaction is disputed
- **THEN** the system returns `clarification` naming the missing datum

#### Scenario: Failure is generic with trace

- **WHEN** the chat pipeline fails unexpectedly
- **THEN** the system returns `error` with a generic message and the request `trace_id`

#### Scenario: Candidates accompany the question

- **WHEN** the customer's stated facts match no single transaction
- **THEN** the clarification lists the candidate transactions with their date, amount, and merchant

### Requirement: Verify-before-claim confirmations

The system SHALL emit `case_confirmation` only after re-reading the created case from the store, and the confirmation SHALL include the case id, transaction facts, state, priority, next steps, expected timeline, `verified_at`, and `verified=true`. The system SHALL never present a merely registered case as resolved. Traces to REQ-0003 (P0, Pending) and REQ-0005 (P0, Pending).

#### Scenario: Confirmation carries re-read proof

- **WHEN** a case is created and re-read successfully
- **THEN** the confirmation matches the stored case field for field with `verified=true`

#### Scenario: No confirmation without verification

- **WHEN** the re-read fails or contradicts the created case
- **THEN** the system never emits `case_confirmation` for that case

### Requirement: Mock orchestrator scenarios

The mock orchestrator SHALL reproduce four demo scenarios: normal (verified confirmation), ambiguous (`clarification`), high-risk (`handoff` that reaches the advisor queue), and failed verification (retry then `handoff`), and SHALL return only intent plus a transaction reference, never invented transaction facts. Each scenario SHALL be labeled as mock-sourced. Traces to REQ-0032 (P1, Pending), REQ-0009 (P0, Pending), REQ-0010 (P0, Pending), and REQ-0011 (P0, Pending).

#### Scenario: Each demo path is reachable

- **WHEN** the demo driver selects a scenario
- **THEN** the chat returns the specified variant and the handoff scenarios create a queue-visible case

#### Scenario: Mock never supplies facts

- **WHEN** the mock decides to open a case
- **THEN** it supplies a transaction reference only, and every displayed fact still comes from the Gold row

## ADDED Requirements

### Requirement: Transaction grounding before creation

The system SHALL open a case only when the customer's stated facts match one Gold transaction exactly on date, amount, and merchant, or when the customer explicitly chooses one of the candidates the system presented. The system SHALL never create a case on a transaction that does not match the customer's stated facts. Grounding SHALL accept Spanish and Portuguese phrasing, including month names in both languages, dispute words such as `cargo`, `cobro`, and `cobrança`, and amounts written in either regional format (`1.000,00` and `1,000.00`). Traces to REQ-0003 (P0, Pending), REQ-0042 (P1, Pending), and REQ-0048 (P0, Pending).

#### Scenario: Exact match opens the case

- **WHEN** the stated date, amount, and merchant match exactly one of the customer's transactions
- **THEN** the system opens a case for that transaction

#### Scenario: Mismatched facts never open a case

- **WHEN** the customer describes an amount, date, or merchant that matches no transaction, or matches more than one
- **THEN** the system returns `clarification` with the candidates and opens nothing

#### Scenario: Explicit choice opens the case

- **WHEN** the customer picks one of the presented candidates or taps a transaction in the interface
- **THEN** the system opens a case for exactly that transaction

#### Scenario: Contradiction is refused

- **WHEN** the stated facts match a transaction but the customer also states a detail that contradicts it (for example a different merchant)
- **THEN** the system asks for confirmation instead of opening a case

#### Scenario: Spanish phrasing grounds correctly

- **WHEN** the customer writes the date with a Spanish month name, a `cargo`, and an amount such as `1.000,00`
- **THEN** the system matches the corresponding transaction

#### Scenario: Portuguese phrasing grounds correctly

- **WHEN** the customer writes a `cobrança` with a Portuguese month name and an amount such as `R$ 1.000,00`
- **THEN** the system matches the corresponding transaction

#### Scenario: Portuguese ambiguity clarifies

- **WHEN** a Portuguese message matches more than one transaction, or none
- **THEN** the system returns `clarification` with the candidates in the customer's language

## ADDED Requirements

### Requirement: Reference date from configuration

The system SHALL read its notion of "today" from the `SENTINEL_REFERENCE_DATE` environment variable, defaulting to `2026-06-17` (the last date in the dataset, since the real clock would make every charge ineligible). The effective value SHALL be shown in the interface and in the receipt. Traces to REQ-0039 (P0, Pending).

#### Scenario: Default reference date is the dataset end

- **WHEN** the variable is unset
- **THEN** the system uses `2026-06-17` and the interface shows that date as the reference

#### Scenario: Environment override wins

- **WHEN** the variable is set to another date
- **THEN** the window check and the displayed date both use it
