# decision-priority Specification

## Purpose

Keeps eligibility and escalation in code, and limits the learned component to the dispute category.

## Requirements

### Requirement: Policy outcome is final
Closed policy rules SHALL be evaluated in code before the learned component and before model wording. A policy hit SHALL NOT be overridden. Pending, Reversed, or Declined status SHALL block a dispute. A request for a person SHALL hand off. Suspected fraud and high amount SHALL hand off only when their country threshold is configured; otherwise those rules SHALL NOT fire. Traces to REQ-0007 (P0, Pending), REQ-0040 (P0, Pending), REQ-0043 (P1, Pending), and REQ-0048 (P0, Done). Decisions 005 and 008.

#### Scenario: Status rule blocks the model
- **WHEN** the selected charge is Reversed and the model proposes opening a dispute
- **THEN** the loop explains the status and does not open a dispute

#### Scenario: Missing threshold is not a rule
- **WHEN** no high-amount threshold is configured for the account country
- **THEN** amount alone does not force a handoff

### Requirement: Learned component fills category only
The learned component SHALL run only after policy has established that a dispute applies. It SHALL assign the category recorded on the dispute and SHALL NOT decide eligibility, confirmation, or escalation. The category set SHALL NOT be hard-coded to a single subcategory. Traces to REQ-0048 (P0, Done) and decision 007.

#### Scenario: Category after allow
- **WHEN** policy allows a dispute on the selected charge
- **THEN** the category port is asked for a category and that value is what the open-dispute call records

#### Scenario: No category call when policy stops
- **WHEN** policy explains a status or hands off
- **THEN** the category port is not called

### Requirement: Model proposes, code executes
The model MAY classify intent and draft wording. It SHALL NOT choose which customer's data is read, SHALL NOT confirm an action, and SHALL NOT supply a customer identifier. A proposed tool call SHALL be checked against policy before it runs. Tools SHALL already be bound to the session. Traces to REQ-0004 (P0, In progress), REQ-0032 (P1, In progress), and REQ-0047 (P0, Pending).

#### Scenario: Injection cannot switch customer
- **WHEN** customer text asks the model to read another customer's charge
- **THEN** the tool still returns only the session-bound charges and no identifier is sent to the model
