# Spec Delta

## MODIFIED Requirements

### Requirement: Structured response variants
Every chat answer SHALL use exactly one variant, validated by a strict model in `app/schemas/chat.py`: `text`, `clarification`, `confirm_box`, `case_confirmation`, `handoff`, or `error`. Replies SHALL carry raw values and translation keys rather than authored prose, and every key SHALL exist in the `es-419` and `pt-BR` locale files. The `error` variant SHALL carry a generic message key plus `trace_id`, never internal details. A `clarification` SHALL carry the candidate transactions the customer can choose from, each marked `eligible` with an `ineligibleKey` when not, and SHALL exclude every id in `rejected_ids`. A `confirm_box` SHALL carry amount, currency, merchant, and date, and SHALL NOT carry a `confirmation_token`. A `handoff` SHALL carry the customer card (reference, reason key, estimated date, source) and the advisor `package`: request intent, verified facts, actions taken, evidence, open questions, language, country, and the derived phase. The package SHALL NOT contain `customer_id` or the customer's raw text. Traces to REQ-0002 (P0, In progress), REQ-0006 (P0, In progress), REQ-0008 (P0, In progress), and REQ-0047 (P0, In progress).

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
- **THEN** the reply carries the package with request, verified facts, actions taken, evidence, open questions, language, country, phase, and no `customer_id` or message text

#### Scenario: Denied candidates are filtered
- **WHEN** a clarification is built after a denial
- **THEN** no id from `rejected_ids` appears in the candidate list

### Requirement: Handoff package covers the whole conversation
The handoff package SHALL carry a `summary` and a `conversation` list with one entry per turn of the session (turn number, what the customer did as a code, the verified charge reference if any, the reply kind and the rule or message key), and `actions_taken` SHALL list every step the system attempted in any turn of the session, failed attempts included, each tagged with its turn. `history` SHALL be bounded to 50 entries and `actions` to 200 entries per session; when the bound is exceeded the oldest entries SHALL be discarded and the stored record SHALL carry an `overflow` mark. The summary SHALL be built deterministically from those entries, never by a model, and SHALL NOT contain the customer's words. A reference that did not resolve to the session customer's charge SHALL NOT appear in the package. The history SHALL be stored with the conversation state and deleted with it. Traces to REQ-0008 (P0, In progress) and REQ-0047 (P0, In progress).

#### Scenario: The advisor sees why and what was tried
- **WHEN** a session ends in `handoff` after several turns
- **THEN** the package lists every turn and every attempted step, including failed read-backs, and its summary names the rule that escalated

#### Scenario: Unknown reference stays out of the ticket
- **WHEN** the customer selected a reference that is not theirs earlier in the session
- **THEN** that reference does not appear anywhere in the package

#### Scenario: Overflow is marked, not silent
- **WHEN** a session exceeds 50 history entries or 200 actions
- **THEN** the oldest entries are discarded and the stored record carries the `overflow` mark

## ADDED Requirements

### Requirement: Repeated ambiguity hands off
After two clarification rounds the next still-ambiguous turn SHALL return `handoff` with reason `fields.missing` instead of a third question. Traces to REQ-0001 (P0, In progress), REQ-0006 (P0, In progress), and REQ-0011 (P0, Pending).

#### Scenario: Third vague turn hands off
- **WHEN** the customer sends a third consecutive vague message
- **THEN** the chat returns `handoff` citing `fields.missing`
