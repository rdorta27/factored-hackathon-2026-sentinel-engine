# Spec Delta

## MODIFIED Requirements

### Requirement: Conversation state survives the turn
The loop SHALL keep, for the life of the session, the bounded turns, the candidates shown, the pending confirmation, the detected language, the clarification count, `person_asks`, and `rejected_ids` (denied or superseded candidate ids). Language SHALL be `es-419` or `pt-BR` and SHALL persist across turns, including a switch between them. The state SHALL NOT contain `customer_id`. The policy engine SHALL NOT store `person_asks`. Traces to REQ-0001 (P0, In progress), REQ-0040 (P0, Pending), and REQ-0047 (P0, Pending).

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
The loop SHALL ask a clarifying question when the charge is missing, up to a maximum of two clarification rounds; the third consecutive vague turn SHALL end in `handoff` with reason `fields.missing` instead of another question. The loop SHALL abstain when the request is out of scope for charges and transactions. It SHALL NOT open a dispute in any of these cases. Traces to REQ-0002 (P0, Pending) and decision 008.

#### Scenario: Ambiguous charge inquiry
- **WHEN** the customer text does not identify a charge
- **THEN** the loop asks what is missing and does not call the open-dispute tool

#### Scenario: Unsupported request
- **WHEN** the customer asks for a balance, a product, a card, or credit
- **THEN** the loop says that is out of scope and offers a handoff

#### Scenario: Third clarification hands off
- **WHEN** the customer sends a third consecutive message that still does not identify a charge
- **THEN** the loop returns a handoff citing `fields.missing` and does not ask again

## ADDED Requirements

### Requirement: Denied charges are not shown again
The loop SHALL exclude every id in `rejected_ids` from the next clarification ranking. A customer denial (`not_mine` on a shown candidate) SHALL append that candidate id to `rejected_ids`. Traces to REQ-0001 (P0, In progress) and REQ-0010 (P0, Pending).

#### Scenario: Denied candidate disappears
- **WHEN** the customer denies a shown charge and the next clarification is built
- **THEN** that charge is absent from the ranked candidates

### Requirement: Correction re-anchors to the repaired candidate
When a turn carries new amount or date facts that match a different charge than the previously shown one, the loop SHALL select the repaired match and SHALL append the superseded id to `rejected_ids`. Traces to REQ-0001 (P0, In progress) and REQ-0003 (P0, Pending).

#### Scenario: Correction with a date wins
- **WHEN** the customer corrects with a date or amount pointing at another charge
- **THEN** the loop selects the newly matched charge and the old one is never shown again

### Requirement: Phase is derived and reported
The loop SHALL derive a phase (`COLLECTING`, `CLARIFYING`, `AWAITING_CONFIRMATION`, `RESOLVED`, `HANDED_OFF`) from the state plus the turn outcome and SHALL expose it on the handoff package and the turn record. The phase SHALL NOT be stored as separate mutable state. Traces to REQ-0001 (P0, In progress) and REQ-0033 (P0, Done).

#### Scenario: Clarifying phase is visible
- **WHEN** a turn ends in a clarification question
- **THEN** the reported phase is `CLARIFYING`
