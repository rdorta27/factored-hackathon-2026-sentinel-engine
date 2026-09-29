# gold-layer Specification

## Purpose

Gives the backend one read seam for transaction eligibility that serves invented mock rows today and DuckDB or Delta Lake rows tomorrow without changing callers.

## Requirements

### Requirement: Denormalized Gold read seam

The system SHALL read transaction eligibility through a single seam returning denormalized rows with transaction date, status, refunded and prior-dispute flags, and an as-of freshness mark. Every read SHALL return its as-of mark alongside the data. Traces to REQ-0039 (P0, Pending) and REQ-0032 (P1, Pending).

#### Scenario: Eligibility read carries freshness

- **WHEN** the disputes service checks a transaction
- **THEN** the row includes the as-of mark that the confirmation can display

#### Scenario: Unknown transaction is not eligible

- **WHEN** the reference matches no Gold row for the session customer
- **THEN** the system treats it as ineligible and offers a handoff

### Requirement: Mock labeled, real deferred

Phase 1 SHALL serve invented rows from an in-memory mock labeled `source=mock`; the DuckDB and Delta Lake adapters SHALL remain a documented later swap with unchanged contracts. Traces to REQ-0032 (P1, Pending) and REQ-0028 (P0, Pending).

#### Scenario: Mock source is visible

- **WHEN** any confirmation is produced in Phase 1
- **THEN** its source field reads `mock`

### Requirement: Per-customer isolation on reads

Gold reads SHALL filter by the session customer; a customer SHALL never see another customer's rows. Traces to REQ-0007 (P0, Pending) and REQ-0047 (P0, Pending).

#### Scenario: Cross-customer reference is invisible

- **WHEN** a customer references another customer's transaction
- **THEN** the lookup behaves as unknown and offers a handoff
