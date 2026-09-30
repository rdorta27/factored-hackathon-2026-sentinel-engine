# Spec Delta

## MODIFIED Requirements

### Requirement: Turn input is text or a structured candidate id

The loop SHALL accept either customer text or a structured candidate id. A free-text affirmation SHALL NOT count as confirmation. A structured candidate id SHALL be a selection when no confirm box is pending, and SHALL be the confirmation only when it matches the pending box and was shown. The loop SHALL NOT open a dispute on the selection meaning. Traces to REQ-0006 (P0, In progress).

#### Scenario: Written yes is not a confirmation

- **WHEN** a confirmation is pending and the customer sends text that means yes
- **THEN** the loop does not open a dispute and the confirmation stays pending

#### Scenario: Button sends the candidate id

- **WHEN** a confirm box is pending and the caller submits that candidate id as a structured field
- **THEN** the loop treats that field as the confirmation, not as customer text

#### Scenario: Structured id without a box is selection

- **WHEN** no confirm box is pending and the caller submits a shown candidate id as a structured field
- **THEN** the loop selects that charge, runs policy, and does not open a dispute

## ADDED Requirements

### Requirement: Grounding selects and does not decide

The loop SHALL use deterministic grounding to choose the charge a statement refers to, and SHALL NOT take an arbitrary first charge. Grounding SHALL run only after a person request and an out-of-scope request have been classified. A matched charge SHALL be input to policy. Pending, Reversed, Declined, an expired window, a repeated person request, and a configured fraud or amount rule SHALL win over the match. Traces to REQ-0003 (P0, Pending), REQ-0042 (P1, Pending), and REQ-0048 (P0, Pending).

#### Scenario: One match does not skip policy

- **WHEN** the statement matches one charge and that charge is Reversed
- **THEN** the loop explains the status and does not show a confirm box

#### Scenario: Several matches ask

- **WHEN** the statement matches more than one charge
- **THEN** the loop asks which charge and does not open a dispute

#### Scenario: Person request is not grounded as a charge

- **WHEN** the customer asks for a person
- **THEN** the loop counts the request and does not select a charge from the wording
