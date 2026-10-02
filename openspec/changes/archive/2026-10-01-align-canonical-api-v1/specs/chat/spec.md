# Spec Delta

## MODIFIED Requirements

### Requirement: Message-only chat request

The system SHALL accept a chat request on `POST /api/v1/chat` carrying the customer message and, optionally, `selected_reference`, and SHALL derive the customer identity exclusively from the session cookie. Those SHALL be the only accepted fields. `selected_reference` SHALL be validated for shape only; authorization SHALL come from resolving it inside the session customer's rows. `selected_reference` SHALL NOT open a dispute by itself. It SHALL be a selection when no confirm box is pending, and the confirmation turn only when it matches the pending box and was shown. A charge from the session customer's transaction panel counts as shown. The system SHALL NOT accept a `confirmation_token` or a `customer_id` in the body. Traces to REQ-0001 (P0, In progress), REQ-0006 (P0, In progress), and REQ-0027 (P0, In progress).

#### Scenario: Chat without session is rejected

- **WHEN** an unauthenticated client posts to `/api/v1/chat`
- **THEN** the system returns 401 and records `access_denied`

#### Scenario: Extra fields are rejected

- **WHEN** a chat body contains any field besides the message and `selected_reference`
- **THEN** the system returns 422 before running any business logic

#### Scenario: Selection shape is format-neutral

- **WHEN** the client selects a transaction whose identifier does not match the mock's format
- **THEN** the request is still accepted and resolved by the session-scoped lookup

#### Scenario: Selection does not open

- **WHEN** the client sends `selected_reference` and no confirm box is pending
- **THEN** the system does not open a dispute

#### Scenario: Pending box makes the same field a confirmation

- **WHEN** a confirm box is pending and `selected_reference` matches that candidate
- **THEN** the system treats the field as the confirmation turn, not as customer text

#### Scenario: Old paths are gone

- **WHEN** a client posts to `/chat` or to any `/auth/*` path
- **THEN** the system returns 404

### Requirement: Structured response variants

Every chat answer SHALL use exactly one variant, validated by a strict model in `app/schemas/chat.py`: `text`, `clarification`, `confirm_box`, `case_confirmation`, `handoff`, or `error`. Replies SHALL carry raw values and translation keys rather than authored prose, and every key SHALL exist in the `es-419` and `pt-BR` locale files. The `error` variant SHALL carry a generic message key plus `trace_id`, never internal details. A `clarification` SHALL carry the candidate transactions the customer can choose from, each marked `eligible` with an `ineligibleKey` when not. A `confirm_box` SHALL carry amount, currency, merchant, and date, and SHALL NOT carry a `confirmation_token`. A `handoff` SHALL carry the customer card (reference, reason key, estimated date, source) and the advisor `package`: request intent, verified facts, actions taken, evidence, open questions, language, and country. The package SHALL NOT contain `customer_id` or the customer's raw text. Traces to REQ-0002 (P0, In progress), REQ-0006 (P0, In progress), REQ-0008 (P0, In progress), and REQ-0047 (P0, In progress).

#### Scenario: Ambiguous request asks instead of guessing

- **WHEN** the request does not identify which transaction is disputed
- **THEN** the system returns `clarification` naming the missing datum

#### Scenario: Failure is generic with trace

- **WHEN** the chat pipeline fails unexpectedly
- **THEN** the system returns `error` with a generic message key and the request `trace_id`

#### Scenario: Candidates accompany the question

- **WHEN** the customer's stated facts match no single transaction
- **THEN** the clarification lists the candidate transactions with their date, amount, and merchant

#### Scenario: Candidates are ranked, capped, and marked

- **WHEN** candidates are returned
- **THEN** they are ordered by similarity to the statement, limited to a small number, and each one states whether it is inside the dispute window

#### Scenario: Allowed charge returns a confirm box

- **WHEN** policy allows a dispute on the selected charge
- **THEN** the system returns `confirm_box` with amount, currency, merchant, and date, and no token

#### Scenario: Handoff carries the advisor package

- **WHEN** the turn ends in `handoff`
- **THEN** the reply carries the package with request, verified facts, actions taken, evidence, open questions, language, and country, and no `customer_id` or message text
