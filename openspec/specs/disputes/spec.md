# disputes Specification

## Purpose

Turns dispute creation into a deterministic, policy-gated operation whose response proves the work done, so the customer trusts the receipt instead of calling to confirm it.

## Requirements

### Requirement: Policy-gated dispute creation

The system SHALL expose `POST /api/v1/disputes/create` for role `customer`, taking a transaction reference and an idempotency key, and SHALL create a case only when code verifies eligibility: within the configured dispute window, transaction not refunded or reversed, and no prior dispute for it. Traces to REQ-0033 (P0, Pending), REQ-0043 (P1, Pending), and REQ-0048 (P0, Pending).

#### Scenario: Eligible transaction opens a case

- **WHEN** a customer requests a dispute for an eligible transaction with a fresh idempotency key
- **THEN** the system creates exactly one case and returns the Proof-of-Work payload

#### Scenario: Stale transaction is refused with reason

- **WHEN** the transaction is older than the dispute window
- **THEN** the system creates no case and returns the ineligibility reason plus a handoff

#### Scenario: Refunded or already-disputed transaction is refused

- **WHEN** the transaction is refunded, reversed, or already disputed
- **THEN** the system creates no case and returns the reason plus a handoff

#### Scenario: Retried request creates no duplicate

- **WHEN** the same idempotency key arrives twice
- **THEN** the system returns the original result without creating a second case

### Requirement: Proof-of-Work payload

Every created case SHALL return the five Proof-of-Work elements: temporary amount hold status, the verified eligibility rule with policy article, the SLA deadline, a downloadable receipt reference, and the human-queue status. The hold SHALL be a simulated status, never real money movement. Traces to REQ-0003 (P0, Pending), REQ-0005 (P0, Pending), and REQ-0004 (P0, Pending).

#### Scenario: Confirmation carries all five elements

- **WHEN** a case is created and verified
- **THEN** the payload contains hold status, rule plus article, SLA deadline, receipt reference, and queue status

#### Scenario: No proof without verification

- **WHEN** the post-creation re-read fails
- **THEN** the system returns a handoff instead of the Proof-of-Work payload

### Requirement: Chat delegates creation

`POST /chat` SHALL NOT invent transaction facts; it SHALL resolve the transaction through the Gold seam and create cases only through the disputes service. Traces to REQ-0003 (P0, Pending) and REQ-0006 (P0, Pending).

#### Scenario: Chat confirmation matches the created case

- **WHEN** the chat flow opens a dispute
- **THEN** the confirmation equals the disputes service result field for field
