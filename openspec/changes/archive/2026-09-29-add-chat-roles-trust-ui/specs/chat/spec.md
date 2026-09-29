# Spec Delta

## Purpose

Gives the authenticated customer a chat endpoint that answers only from verified store reads and proves it, so a dispute confirmation is evidence instead of a promise.

## ADDED Requirements

### Requirement: Message-only chat request

The system SHALL accept a chat request carrying only the customer message and SHALL derive the customer identity exclusively from the session. Traces to REQ-0001 (P0, Pending) and REQ-0027 (P0, Pending).

#### Scenario: Chat without session is rejected

- **WHEN** an unauthenticated client posts to `/chat`
- **THEN** the system returns 401 and records `access_denied`

#### Scenario: Extra fields are rejected

- **WHEN** a chat body contains any field besides the message
- **THEN** the system returns 422 before running any business logic

### Requirement: Structured response variants

Every chat answer SHALL use exactly one variant: `text`, `clarification`, `case_confirmation`, `handoff`, or `error`. The `error` variant SHALL carry a generic message plus `trace_id`, never internal details. Traces to REQ-0002 (P0, Pending) and REQ-0006 (P0, Pending).

#### Scenario: Ambiguous request asks instead of guessing

- **WHEN** the request does not identify which transaction is disputed
- **THEN** the system returns `clarification` naming the missing datum

#### Scenario: Failure is generic with trace

- **WHEN** the chat pipeline fails unexpectedly
- **THEN** the system returns `error` with a generic message and the request `trace_id`

### Requirement: Verify-before-claim confirmations

The system SHALL emit `case_confirmation` only after re-reading the created case from the store, and the confirmation SHALL include the case id, transaction facts, state, priority, next steps, expected timeline, `verified_at`, and `verified=true`. The system SHALL never present a merely registered case as resolved. Traces to REQ-0003 (P0, Pending) and REQ-0005 (P0, Pending).

#### Scenario: Confirmation carries re-read proof

- **WHEN** a case is created and re-read successfully
- **THEN** the confirmation matches the stored case field for field with `verified=true`

#### Scenario: No confirmation without verification

- **WHEN** the re-read fails or contradicts the created case
- **THEN** the system never emits `case_confirmation` for that case

### Requirement: Bounded retries then handoff

When creation or verification fails, the system SHALL retry a bounded number of times and then return `handoff` instead of failing silently or claiming success. Traces to REQ-0026 (P1, Pending) and REQ-0011 (P0, Pending).

#### Scenario: Persistent failure becomes a handoff

- **WHEN** retries are exhausted without a verified case
- **THEN** the system returns `handoff` with reason, what the advisor receives, and estimated time

### Requirement: Agent request escalates

When the customer asks to speak to a person, the system SHALL make a single offer to help and, if they insist, SHALL escalate immediately via `handoff`. Traces to REQ-0040 (P0, Pending).

#### Scenario: Insistent customer reaches a human

- **WHEN** the customer repeats the request for a person after one offer of help
- **THEN** the system returns `handoff` without further persuasion attempts

### Requirement: Mock orchestrator scenarios

The mock orchestrator SHALL reproduce four demo scenarios: normal (verified confirmation), ambiguous (`clarification`), high-risk (`handoff` that reaches the advisor queue), and failed verification (retry then `handoff`). Each scenario SHALL be labeled as mock-sourced. Traces to REQ-0032 (P1, Pending), REQ-0009 (P0, Pending), REQ-0010 (P0, Pending), and REQ-0011 (P0, Pending).

#### Scenario: Each demo path is reachable

- **WHEN** the demo driver selects a scenario
- **THEN** the chat returns the specified variant and the handoff scenarios create a queue-visible case
