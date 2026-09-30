# orchestrator-loop Specification

## Purpose

Runs one conversation turn of the charge-inquiry loop and keeps the state the next turn needs.

## Requirements

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

### Requirement: Conversation state survives the turn
The loop SHALL keep, for the life of the session, the bounded turns, the candidates shown, the pending confirmation, the detected language, the clarification count, and `person_asks`. Language SHALL be `es-419` or `pt-BR`. The state SHALL NOT contain `customer_id`. The policy engine SHALL NOT store `person_asks`. Traces to REQ-0001 (P0, Pending), REQ-0040 (P0, Pending), and REQ-0047 (P0, Pending).

#### Scenario: Next turn sees the candidates already shown
- **WHEN** a turn shows candidate charges and a later turn arrives on the same session
- **THEN** those candidates are still available and no customer identifier is in the state

#### Scenario: Person asks survive the turn
- **WHEN** the customer asks for a person and a later turn arrives on the same session
- **THEN** `person_asks` is still the count from the previous turn

### Requirement: A turn stops when it cannot yet act
The loop SHALL ask a clarifying question when the charge is missing, and SHALL abstain when the request is out of scope for charges and transactions. It SHALL NOT open a dispute in either case. Traces to REQ-0002 (P0, Pending) and decision 008.

#### Scenario: Ambiguous charge inquiry
- **WHEN** the customer text does not identify a charge
- **THEN** the loop asks what is missing and does not call the open-dispute tool

#### Scenario: Unsupported request
- **WHEN** the customer asks for a balance, a product, a card, or credit
- **THEN** the loop says that is out of scope and offers a handoff

### Requirement: Demo outcomes are structural
The three demo cases SHALL be distinguishable by outcome, in both `es-419` and `pt-BR`: a confirmed dispute yields a case number only after read-back, an ambiguous or unsupported request does not open a dispute, and a repeated request for a person yields a handoff. The first request SHALL offer help and SHALL NOT hand off. Traces to REQ-0009, REQ-0010, REQ-0011 (all P0, Pending), and REQ-0040 (P0, Pending).

#### Scenario: Normal case in either reply language
- **WHEN** policy allows a dispute and the caller confirms the shown candidate
- **THEN** the outcome is a case number and the reply language is the detected `es-419` or `pt-BR`

#### Scenario: Human case
- **WHEN** the customer asks for a person a second time on the same session
- **THEN** the outcome is a handoff and no case number

#### Scenario: First person request is not the human case
- **WHEN** the customer asks for a person for the first time
- **THEN** the outcome is an offer to keep helping and no handoff is opened

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
