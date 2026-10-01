# Spec Delta

## ADDED Requirements

### Requirement: Two-step dispute API

The system SHALL expose `POST /api/v1/disputes/preview` and `POST /api/v1/disputes` for the session customer. The preview SHALL take a charge reference and an optional reason (at most 300 characters), SHALL run the same orchestrator step and policy as the chat, and SHALL return a `confirm_box`, a `text` explanation or a `handoff` without writing. The create SHALL open a dispute only for the charge whose preview is pending, SHALL return `case_confirmation` only after read-back (201), and SHALL return 409 when no preview is pending for that charge. The reason SHALL be stored with the case and SHALL NOT be logged or returned. Bodies SHALL reject any other field, including `customer_id` and `confirmation_token`. Traces to REQ-0004 (P0, In progress), REQ-0005 (P0, Done), REQ-0006 (P0, In progress), and REQ-0033 (P0, Done).

#### Scenario: Preview never writes

- **WHEN** a customer previews an eligible charge
- **THEN** the system returns `confirm_box` and the customer's case list is unchanged

#### Scenario: Create without preview is refused

- **WHEN** a customer creates a dispute with no pending preview for that charge
- **THEN** the system returns 409 and writes nothing

#### Scenario: Policy decides the preview

- **WHEN** the charge is reversed, declined, pending, out of the window or already disputed
- **THEN** the preview returns the explanation and a later create returns 409

#### Scenario: Foreign charge is unknown

- **WHEN** the reference belongs to another customer
- **THEN** the preview returns `handoff` without any of that charge's facts

### Requirement: Dispute case listing

The system SHALL expose `GET /api/v1/disputes` and `GET /api/v1/disputes/{case_id}` returning the session customer's cases: disputes and handoff tickets, newest first, each with case id, kind, status (dataset complaints vocabulary: Open, Escalated), transaction facts when known, reason key and creation time. The response SHALL NOT contain `customer_id`, the customer's reason or the advisor package. Another customer's case SHALL be a 404 indistinguishable from a missing one. A `customer_id` query parameter SHALL be rejected. Traces to REQ-0003 (P0, In progress), REQ-0007 (P0, In progress), and REQ-0047 (P0, In progress).

#### Scenario: Customer sees own cases

- **WHEN** a customer with one dispute and one handoff lists cases
- **THEN** both appear with kind and status, and nothing identifies the customer

#### Scenario: Another customer's case is invisible

- **WHEN** a customer requests a case id that belongs to someone else
- **THEN** the system returns 404

### Requirement: One open dispute per charge

The system SHALL keep at most one open dispute per charge and customer, whichever session or entry point asks. Idempotency SHALL be scoped to an opaque hash of the customer, never to the session token and never to the identifier itself. A charge with an open case SHALL be treated as already disputed by the policy, and a repeated create SHALL return the existing case. Traces to REQ-0026 (P1, Done) and REQ-0005 (P0, Done).

#### Scenario: A new session cannot duplicate a dispute

- **WHEN** a customer disputes a charge, logs out, logs in again and asks to dispute it again
- **THEN** the system answers `already.disputed` and the case list still holds one dispute for that charge
