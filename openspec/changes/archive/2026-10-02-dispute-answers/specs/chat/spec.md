## MODIFIED Requirements

### Requirement: Structured response variants

Every chat answer SHALL use exactly one variant, validated by a strict model in `app/schemas/chat.py`: `text`, `clarification`, `confirm_box`, `case_confirmation`, `handoff`, `explanation`, or `error`. Replies SHALL carry raw values and translation keys rather than authored prose, and every key SHALL exist in the `es-419` and `pt-BR` locale files. The `error` variant SHALL carry a generic message key plus `trace_id`, never internal details. A `clarification` SHALL carry the candidate transactions the customer can choose from, each marked `eligible` with an `ineligibleKey` when not, and SHALL exclude every id in `rejected_ids`. A `confirm_box` SHALL carry amount, currency, merchant, and date, and SHALL NOT carry a `confirmation_token`. A `handoff` SHALL carry the customer card (reference, reason key, estimated date, source) and the advisor `package`: request intent, verified facts, actions taken, evidence, open questions, language, country, and the derived phase. The package SHALL NOT contain `customer_id` or the customer's raw text. An `explanation` SHALL carry a message key, the `rule_id` it explains and only verified values from the stored decision; it SHALL NOT carry `customer_id` or the customer's text. Traces to REQ-0002 (P0, In progress), REQ-0006 (P0, In progress), REQ-0008 (P0, In progress), REQ-0033 (P0, Done), and REQ-0047 (P0, In progress).

#### Scenario: Ambiguous request asks instead of guessing

- **WHEN** the request does not identify which transaction is disputed
- **THEN** the system returns `clarification` naming the missing datum

#### Scenario: Failure is generic with trace

- **WHEN** the chat pipeline fails unexpectedly
- **THEN** the system returns `error` with a generic message key and the request `trace_id`

#### Scenario: Candidates accompany the question

- **WHEN** the customer's stated facts match no single transaction
- **THEN** the clarification lists the candidate transactions with their date, amount, and merchant

#### Scenario: Denied candidates are filtered

- **WHEN** a clarification is built after a denial
- **THEN** no id from `rejected_ids` appears in the candidate list

#### Scenario: Candidates are ranked, capped, and marked

- **WHEN** candidates are returned
- **THEN** they are ordered by similarity to the statement, limited to a small number, and each one states whether it is inside the dispute window

#### Scenario: Allowed charge returns a confirm box

- **WHEN** policy allows a dispute on the selected charge
- **THEN** the system returns `confirm_box` with amount, currency, merchant, and date, and no token

#### Scenario: Handoff carries the advisor package

- **WHEN** the turn ends in `handoff`
- **THEN** the reply carries the package with request, verified facts, actions taken, evidence, open questions, language, country, phase, and no `customer_id` or message text

#### Scenario: A why follow-up returns an explanation

- **WHEN** the customer asks why after a policy decision
- **THEN** the system returns `explanation` with the rule and its verified values, and no `customer_id`
