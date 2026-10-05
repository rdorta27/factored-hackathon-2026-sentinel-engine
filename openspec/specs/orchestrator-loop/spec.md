# orchestrator-loop Specification

## Purpose

Runs one conversation turn of the charge-inquiry loop and keeps the state the next turn needs.

## Requirements

### Requirement: Turn input is text or a structured candidate id
The loop SHALL accept either customer text or a structured candidate id. A free-text affirmation SHALL NOT count as confirmation. A structured candidate id SHALL be a selection when no confirm box is pending, and SHALL be the confirmation only when it matches the pending box and was shown. The loop SHALL NOT open a dispute on the selection meaning. Traces to REQ-0006 (P0, Done).

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
The loop SHALL keep, for the life of the session, the bounded turns, the candidates shown, the pending confirmation, the detected language, the clarification count, `person_asks`, and `rejected_ids` (denied or superseded candidate ids). Language SHALL be `es-419` or `pt-BR` and SHALL persist across turns, including a switch between them. The state SHALL NOT contain `customer_id`. The policy engine SHALL NOT store `person_asks`. Traces to REQ-0001 (P0, Done), REQ-0040 (P0, Done), and REQ-0047 (P0, Done).

#### Scenario: Next turn sees the candidates already shown
- **WHEN** a turn shows candidate charges and a later turn arrives on the same session
- **THEN** those candidates are still available and no customer identifier is in the state

#### Scenario: Person asks survive the turn
- **WHEN** the customer asks for a person and a later turn arrives on the same session
- **THEN** `person_asks` is still the count from the previous turn

#### Scenario: Rejected ids survive the turn
- **WHEN** a candidate was denied or superseded on an earlier turn
- **THEN** its id is still present in `rejected_ids` on the next turn

#### Scenario: Language persists across a switch
- **WHEN** the customer switches from es-419 to pt-BR (or back) mid-session
- **THEN** the detected language follows the latest turn and stays stable for the following turns

### Requirement: A turn stops when it cannot yet act
The loop SHALL ask a clarifying question when the charge is missing, up to a maximum of two clarification rounds; the third consecutive vague turn SHALL end in `handoff` with reason `fields.missing` instead of another question. The loop SHALL abstain when the request is out of scope for charges and transactions. It SHALL NOT open a dispute in any of these cases. Traces to REQ-0002 (P0, Done) and decision 008.

#### Scenario: Ambiguous charge inquiry
- **WHEN** the customer text does not identify a charge
- **THEN** the loop asks what is missing and does not call the open-dispute tool

#### Scenario: Unsupported request
- **WHEN** the customer asks for a balance, a product, a card, or credit
- **THEN** the loop says that is out of scope and offers a handoff

#### Scenario: Third clarification hands off
- **WHEN** the customer sends a third consecutive message that still does not identify a charge
- **THEN** the loop returns a handoff citing `fields.missing` and does not ask again

### Requirement: Demo outcomes are structural
The three demo cases SHALL be distinguishable by outcome, in both `es-419` and `pt-BR`: a confirmed dispute yields a case number only after read-back, an ambiguous or unsupported request does not open a dispute, and a repeated request for a person yields a handoff. The first request SHALL offer help and SHALL NOT hand off. Traces to REQ-0009, REQ-0010, REQ-0011 (all P0, Pending), and REQ-0040 (P0, Done).

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
The loop SHALL use deterministic grounding to choose the charge a statement refers to, and SHALL NOT take an arbitrary first charge. Grounding SHALL run only after a person request and an out-of-scope request have been classified. A matched charge SHALL be input to policy. Pending, Reversed, Declined, an expired window, a repeated person request, and a configured fraud or amount rule SHALL win over the match. Traces to REQ-0003 (P0, Done), REQ-0042 (P1, Done), and REQ-0048 (P0, Done).

#### Scenario: One match does not skip policy
- **WHEN** the statement matches one charge and that charge is Reversed
- **THEN** the loop explains the status and does not show a confirm box

#### Scenario: Several matches ask
- **WHEN** the statement matches more than one charge
- **THEN** the loop asks which charge and does not open a dispute

#### Scenario: Person request is not grounded as a charge
- **WHEN** the customer asks for a person
- **THEN** the loop counts the request and does not select a charge from the wording

### Requirement: Denied charges are not shown again
The loop SHALL exclude every id in `rejected_ids` from the next clarification ranking. A customer denial (`not_mine` on a shown candidate) SHALL append that candidate id to `rejected_ids`. Traces to REQ-0001 (P0, Done) and REQ-0010 (P0, Done).

#### Scenario: Denied candidate disappears
- **WHEN** the customer denies a shown charge and the next clarification is built
- **THEN** that charge is absent from the ranked candidates

### Requirement: Correction re-anchors to the repaired candidate
When a turn carries new amount or date facts that match a different charge than the previously shown one, the loop SHALL select the repaired match and SHALL append the superseded id to `rejected_ids`. Traces to REQ-0001 (P0, Done) and REQ-0003 (P0, Done).

#### Scenario: Correction with a date wins
- **WHEN** the customer corrects with a date or amount pointing at another charge
- **THEN** the loop selects the newly matched charge and the old one is never shown again

### Requirement: Phase is derived and reported
The loop SHALL derive a phase (`collecting`, `clarifying`, `awaiting_confirmation`, `resolved`, `handed_off`) from the state plus the turn outcome and SHALL expose it on the handoff package and the turn record. The phase SHALL NOT be stored as separate mutable state. Traces to REQ-0001 (P0, Done) and REQ-0033 (P0, Done).

#### Scenario: Clarifying phase is visible
- **WHEN** a turn ends in a clarification question
- **THEN** the reported phase is `clarifying`
