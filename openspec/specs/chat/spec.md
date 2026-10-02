# chat Specification

## Purpose

Gives the authenticated customer a chat endpoint that answers only from verified store reads and proves it, so a dispute confirmation is evidence instead of a promise.

## Requirements

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

### Requirement: Verify-before-claim confirmations

The system SHALL emit `case_confirmation` only after re-reading the created case from the store, and the confirmation SHALL include the case id, transaction facts, `verified_at`, `verified=true`, the reference date, a rule key, a no-funds key, and `source=mock`. The system SHALL never present a merely registered case as resolved. The confirmation SHALL NOT require a priority, a service-level deadline, a queue status, or a receipt download. Traces to REQ-0003 (P0, Pending) and REQ-0005 (P0, Pending).

#### Scenario: Confirmation carries re-read proof

- **WHEN** a case is created and re-read successfully
- **THEN** the confirmation matches the stored case field for field with `verified=true`

#### Scenario: No confirmation without verification

- **WHEN** the re-read fails or contradicts the created case
- **THEN** the system never emits `case_confirmation` for that case

#### Scenario: Next step names the real deadline

- **WHEN** the confirmation is rendered
- **THEN** the next step is a translation key, the card shows the reference date, and it does not claim a service-level deadline or a funds hold

### Requirement: Bounded retries then handoff

When creation or verification fails, the system SHALL retry a bounded number of times and then return `handoff` instead of failing silently or claiming success. Traces to REQ-0026 (P1, Pending) and REQ-0011 (P0, Pending).

#### Scenario: Persistent failure becomes a handoff

- **WHEN** retries are exhausted without a verified case
- **THEN** the system returns `handoff` with the reason key and the advisor reference

### Requirement: Agent request escalates

When the customer asks to speak to a person, the system SHALL make a single offer to help and, if they insist, SHALL escalate immediately via `handoff`. Traces to REQ-0040 (P0, Pending).

#### Scenario: Insistent customer reaches a human

- **WHEN** the customer repeats the request for a person after one offer of help
- **THEN** the system returns `handoff` without further persuasion attempts

### Requirement: Transaction grounding before creation

The system SHALL select a charge only when the customer's stated facts match one transaction exactly on date, amount, and merchant, or when the customer sends `selected_reference` for one shown candidate. The system SHALL never open a dispute on that selection alone, and SHALL never create a case on a transaction that does not match the customer's stated facts or was not explicitly selected. Grounding SHALL accept Spanish and Portuguese phrasing, including month names in both languages, dispute words such as `cargo` (a charge), `cobro` (a charge), and `cobrança` (a charge), and amounts written in either regional format (`1.000,00` and `1,000.00`). A person request or an out-of-scope request SHALL be classified before grounding. Traces to REQ-0003 (P0, Pending), REQ-0042 (P1, Pending), and REQ-0048 (P0, Pending).

#### Scenario: Exact match opens the case

- **WHEN** the stated date, amount, and merchant match exactly one of the customer's transactions
- **THEN** the system selects that transaction and does not open a dispute on that turn

#### Scenario: Mismatched facts never open a case

- **WHEN** the customer describes an amount, date, or merchant that matches no transaction, or matches more than one
- **THEN** the system returns `clarification` with the candidates and opens nothing

#### Scenario: Explicit choice opens the case

- **WHEN** the customer picks one of the presented candidates or taps a transaction in the interface
- **THEN** the system selects exactly that transaction and does not open a dispute on that turn

#### Scenario: Contradiction is refused

- **WHEN** the stated facts match a transaction but the customer also states a detail that contradicts it (for example a different merchant)
- **THEN** the system asks for clarification instead of opening a case

#### Scenario: Spanish phrasing grounds correctly

- **WHEN** the customer writes the date with a Spanish month name, a `cargo`, and an amount such as `1.000,00`
- **THEN** the system matches the corresponding transaction

#### Scenario: Portuguese phrasing grounds correctly

- **WHEN** the customer writes a `cobrança` with a Portuguese month name and an amount such as `R$ 1.000,00`
- **THEN** the system matches the corresponding transaction

#### Scenario: Portuguese ambiguity clarifies

- **WHEN** a Portuguese message matches more than one transaction, or none
- **THEN** the system returns `clarification` with the candidates in the customer's language

### Requirement: Demo outcomes on the chat endpoint

The chat endpoint SHALL make three outcomes distinguishable, in both `es-419` and `pt-BR`: a confirmed dispute yields `case_confirmation` only after read-back, an ambiguous or unsupported request does not open a dispute, and a repeated request for a person yields `handoff`. The first request for a person SHALL offer help and SHALL NOT hand off. Displayed transaction facts SHALL come from the session customer's rows. Each mock-sourced confirmation SHALL be labeled `source=mock`. Traces to REQ-0032 (P1, Pending), REQ-0009 (P0, Pending), REQ-0010 (P0, Pending), REQ-0011 (P0, Pending), and REQ-0040 (P0, Pending).

#### Scenario: Normal case after confirmation

- **WHEN** policy allows a dispute and the caller confirms the shown candidate
- **THEN** the chat returns `case_confirmation` only after read-back, labeled `source=mock`

#### Scenario: Ambiguous case does not open

- **WHEN** the message does not identify one charge
- **THEN** the chat returns `clarification` and opens nothing

#### Scenario: Handoff is not a queue write

- **WHEN** verification fails or the customer asks for a person a second time
- **THEN** the chat returns `handoff` and does not require an advisor queue

### Requirement: Handoff filed as a ticket

Every `handoff` reply SHALL be filed as a case with `kind=handoff`, `status=Escalated`, the reply's reference and reason key, and the full advisor package, so the human side receives the ticket and why it was raised. Traces to REQ-0008 (P0, In progress) and REQ-0011 (P0, In progress).

#### Scenario: Insistent customer leaves a ticket

- **WHEN** the customer asks for a person a second time
- **THEN** the case list shows an escalated handoff with the reply's reference, and the stored package equals the reply's package

### Requirement: Handoff package covers the whole conversation

The handoff package SHALL carry a `summary` and a `conversation` list with one entry per turn of the session (turn number, what the customer did as a code, the verified charge reference if any, the reply kind and the rule or message key), and `actions_taken` SHALL list every step the system attempted in any turn of the session, failed attempts included, each tagged with its turn. The summary SHALL be built deterministically from those entries, never by a model, and SHALL NOT contain the customer's words. A reference that did not resolve to the session customer's charge SHALL NOT appear in the package. The history SHALL be stored with the conversation state and deleted with it. Traces to REQ-0008 (P0, In progress) and REQ-0047 (P0, In progress).

#### Scenario: The advisor sees why and what was tried

- **WHEN** a session ends in `handoff` after several turns
- **THEN** the package lists every turn and every attempted step, including failed read-backs, and its summary names the rule that escalated

#### Scenario: Unknown reference stays out of the ticket

- **WHEN** the customer selected a reference that is not theirs earlier in the session
- **THEN** that reference does not appear anywhere in the package
