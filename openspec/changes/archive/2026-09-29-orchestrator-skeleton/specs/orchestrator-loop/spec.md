# Spec Delta

## Purpose

Runs one conversation turn of the charge-inquiry loop and keeps the state the next turn needs.

## ADDED Requirements

### Requirement: Turn input is text or a structured candidate id
The loop SHALL accept either customer text or a structured candidate id. A free-text affirmation SHALL NOT count as confirmation. Traces to REQ-0006 (P0, In progress).

#### Scenario: Written yes is not a confirmation
- **WHEN** a confirmation is pending and the customer sends text that means yes
- **THEN** the loop does not open a dispute and the confirmation stays pending

#### Scenario: Button sends the candidate id
- **WHEN** the caller submits the candidate id of a shown charge as a structured field
- **THEN** the loop treats that field as the confirmation, not as customer text

### Requirement: Conversation state survives the turn
The loop SHALL keep, for the life of the session, the bounded turns, the candidates shown, the pending confirmation, the detected language, and the clarification count. Language SHALL be `es-419` or `pt-BR`. The state SHALL NOT contain `customer_id`. Traces to REQ-0001 (P0, Pending) and REQ-0047 (P0, Pending).

#### Scenario: Next turn sees the candidates already shown
- **WHEN** a turn shows candidate charges and a later turn arrives on the same session
- **THEN** those candidates are still available and no customer identifier is in the state

### Requirement: A turn stops when it cannot yet act
The loop SHALL ask a clarifying question when the charge is missing, and SHALL abstain when the request is out of scope for charges and transactions. It SHALL NOT open a dispute in either case. Traces to REQ-0002 (P0, Pending) and decision 008.

#### Scenario: Ambiguous charge inquiry
- **WHEN** the customer text does not identify a charge
- **THEN** the loop asks what is missing and does not call the open-dispute tool

#### Scenario: Unsupported request
- **WHEN** the customer asks for a balance, a product, a card, or credit
- **THEN** the loop says that is out of scope and offers a handoff

### Requirement: Demo outcomes are structural
The three demo cases SHALL be distinguishable by outcome, in both `es-419` and `pt-BR`: a confirmed dispute yields a case number only after read-back, an ambiguous or unsupported request does not open a dispute, and a human request yields a handoff. Traces to REQ-0009, REQ-0010, and REQ-0011 (all P0, Pending).

#### Scenario: Normal case in either reply language
- **WHEN** policy allows a dispute and the caller confirms the shown candidate
- **THEN** the outcome is a case number and the reply language is the detected `es-419` or `pt-BR`

#### Scenario: Human case
- **WHEN** the customer asks for a person
- **THEN** the outcome is a handoff and no case number
