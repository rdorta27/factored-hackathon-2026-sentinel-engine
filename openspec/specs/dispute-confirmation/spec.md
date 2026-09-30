# dispute-confirmation Specification

## Purpose

Stops a dispute from being opened or reported until the customer confirms and the store read-back succeeds.

## Requirements

### Requirement: Confirm box before any write

When policy allows a dispute, the loop SHALL show the selected candidate (amount, currency, merchant, date) and stop. It SHALL NOT issue a `confirmation_token` or call the open-dispute tool on that turn. An exact match and a structured selection SHALL end in that box when policy allows, and SHALL NOT open a dispute on the selection turn. Traces to REQ-0006 (P0, In progress) and REQ-0043 (P1, Pending).

#### Scenario: Approved charge waits for the button
- **WHEN** the selected charge is Approved, inside the filing window, and no stop rule applies
- **THEN** the turn ends with a confirm box and no dispute write

#### Scenario: Status blocks the box
- **WHEN** the selected charge is Pending, Reversed, or Declined
- **THEN** the loop explains the status and does not show a confirm box

#### Scenario: Tap waits for the button
- **WHEN** the customer selects a shown charge and no confirm box is pending yet
- **THEN** the turn does not open a dispute

### Requirement: Token authorizes the confirmation turn
On the confirmation turn the loop SHALL issue one single-use `confirmation_token` bound to the session, the candidate, and the action, and SHALL pass it to the open-dispute tool. The model SHALL NOT see, create, or forward the token. The token SHALL NOT appear in the chat request or the chat response. A candidate id that was not shown SHALL be rejected without a write. A structured selection while no box is pending SHALL NOT issue a token. Traces to REQ-0006 (P0, In progress) and REQ-0047 (P0, Pending).

#### Scenario: Matching candidate id opens once
- **WHEN** the structured candidate id matches the pending confirmation
- **THEN** the open-dispute tool is called with a token the model never received

#### Scenario: Unknown candidate id
- **WHEN** the structured candidate id was not among the candidates shown
- **THEN** the loop does not call the open-dispute tool

#### Scenario: Selection turn issues no token
- **WHEN** the structured candidate id arrives and no confirm box is pending
- **THEN** the loop does not issue a token and does not call the open-dispute tool

### Requirement: Same key, bounded read-back
The idempotency key SHALL be derived from session, candidate, and action, not from the request trace. A retry with that key SHALL return the existing dispute. The loop SHALL read the dispute back and SHALL retry a failed write or read-back at most three times with the same key. A case number SHALL be reported only when the read-back finds the record. Otherwise the loop SHALL hand off and record the attempt count, with no case number. Traces to REQ-0005 (P0, Pending), REQ-0008 (P0, In progress), and REQ-0026 (P1, Pending).

#### Scenario: Read-back succeeds
- **WHEN** the open-dispute call returns and a later lookup finds the record within three attempts
- **THEN** the customer receives that case number and a second confirmation of the same candidate does not create another dispute

#### Scenario: Read-back never succeeds
- **WHEN** the lookup fails on all three attempts
- **THEN** the outcome is a handoff that includes the attempt count and no case number
