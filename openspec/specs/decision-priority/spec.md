# decision-priority Specification

## Purpose

Keeps eligibility and escalation in code, and limits the learned component to the dispute category.

## Requirements

### Requirement: Policy outcome is final
Closed policy rules SHALL be evaluated in code before the learned component and before model wording. A policy hit SHALL NOT be overridden. Pending, Reversed, or Declined status SHALL block a dispute. The first request for a person SHALL offer help and SHALL NOT open a dispute. A repeated request SHALL hand off. Suspected fraud SHALL hand off citing `fraud.claim` when the customer explicitly states the charge was not theirs, and citing `fraud.score` when the charge's fraud score is above the threshold configured for its account country and currency. High amount SHALL hand off when the amount is above the threshold for its account country and currency. A rule with no configured value for that currency SHALL NOT fire. Traces to REQ-0006 (P0, Done), REQ-0007 (P0, Done), REQ-0040 (P0, Done), REQ-0043 (P1, Done), and REQ-0048 (P0, Done). Decisions 005, 008, 25 and 26.

#### Scenario: Status rule blocks the model
- **WHEN** the selected charge is Reversed and the model proposes opening a dispute
- **THEN** the loop explains the status and does not open a dispute

#### Scenario: Missing threshold is not a rule
- **WHEN** no high-amount threshold is configured for the account country and the charge currency
- **THEN** amount alone does not force a handoff

#### Scenario: First request offers help
- **WHEN** the customer asks for a person and `person_asks` is 1
- **THEN** the outcome is an offer to keep helping and no dispute is opened

#### Scenario: Repeated request hands off
- **WHEN** the customer asks for a person again and `person_asks` is at least 2
- **THEN** the outcome is a handoff and the cited rule is `person.insist`

#### Scenario: Not-mine claim hands off
- **WHEN** the customer says the charge was not theirs and the charge is Approved and inside the window
- **THEN** the outcome is a handoff citing `fraud.claim` and no dispute is opened

#### Scenario: Unrecognized charge is not a fraud claim
- **WHEN** the customer only says they do not recognize the charge
- **THEN** the fraud rule does not fire on wording and the normal dispute path continues

### Requirement: Filing window is recomputed at request time
A charge SHALL be disputable only when its age in days, from the injected demo date to the transaction date, is less than or equal to the country window. Day 90 SHALL allow a dispute. Day 91 SHALL NOT. The Gold flag `is_eligible_for_dispute` SHALL be a hint only. If it disagrees with the recomputed age, the recomputed age SHALL win. An expired window SHALL explain the rule and offer a handoff, and SHALL NOT open a dispute. Traces to REQ-0043 (P1, Done) and decision 003.

#### Scenario: Day 90 is inside the window
- **WHEN** the selected charge is Approved and its age is 90 days
- **THEN** the window rule does not block the dispute

#### Scenario: Day 91 expires the window
- **WHEN** the selected charge is Approved and its age is 91 days
- **THEN** the outcome cites `window.expired`, explains the rule, offers a handoff, and does not open a dispute

#### Scenario: Gold hint loses
- **WHEN** Gold marks the charge eligible and the recomputed age is 91 days
- **THEN** the outcome is `window.expired`

### Requirement: Learned component fills category only
The learned component SHALL run only after policy has established that a dispute applies. It SHALL assign the category recorded on the dispute and SHALL NOT decide eligibility, confirmation, or escalation. The category set SHALL NOT be hard-coded to a single subcategory. Traces to REQ-0048 (P0, Done) and decision 007.

#### Scenario: Category after allow
- **WHEN** policy allows a dispute on the selected charge
- **THEN** the category port is asked for a category and that value is what the open-dispute call records

#### Scenario: No category call when policy stops
- **WHEN** policy explains a status or hands off
- **THEN** the category port is not called

### Requirement: Model proposes, code executes
The model MAY classify intent and draft wording. It SHALL NOT choose which customer's data is read, SHALL NOT confirm an action, and SHALL NOT supply a customer identifier. A proposed tool call SHALL be checked against policy before it runs. Tools SHALL already be bound to the session. Traces to REQ-0004 (P0, Done), REQ-0032 (P1, Done), and REQ-0047 (P0, Done).

#### Scenario: Injection cannot switch customer
- **WHEN** customer text asks the model to read another customer's charge
- **THEN** the tool still returns only the session-bound charges and no identifier is sent to the model
