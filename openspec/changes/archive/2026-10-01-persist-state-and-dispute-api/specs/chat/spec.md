# Spec Delta

## ADDED Requirements

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
