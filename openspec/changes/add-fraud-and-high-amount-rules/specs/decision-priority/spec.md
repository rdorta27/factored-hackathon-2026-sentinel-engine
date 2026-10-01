## MODIFIED Requirements

### Requirement: Policy outcome is final
Closed policy rules SHALL be evaluated in code before the learned component and before model wording. A policy hit SHALL NOT be overridden. Pending, Reversed, or Declined status SHALL block a dispute. The first request for a person SHALL offer help and SHALL NOT open a dispute. A repeated request SHALL hand off. Suspected fraud SHALL hand off citing `fraud.claim` when the customer explicitly states the charge was not theirs, and citing `fraud.score` when the charge's fraud score is above the threshold configured for its account country and currency. High amount SHALL hand off when the amount is above the threshold for its account country and currency. A rule with no configured value for that currency SHALL NOT fire. Traces to REQ-0006 (P0, In progress), REQ-0007 (P0, Done), REQ-0040 (P0, In progress), REQ-0043 (P1, Done), and REQ-0048 (P0, Done). Decisions 005, 008, 25 and 26.

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
