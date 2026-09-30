# Spec Delta

## MODIFIED Requirements

### Requirement: Receipt card with timeline

A `case_confirmation` SHALL render as a receipt card whose first line states the outcome in plain language, followed by a large case number, then what happens next, and finally the detail. Amounts SHALL show the transaction's own currency with its code visible, dates SHALL follow one shared locale-aware format, and the card SHALL state that no funds were held or moved. The card SHALL show the reference date. The card SHALL NOT require a receipt download. Traces to REQ-0003 (P0, Pending), REQ-0041 (P0, Pending), and REQ-0004 (P0, Pending).

#### Scenario: Confirmation is visually distinct

- **WHEN** a verified confirmation arrives
- **THEN** the card shows the verified check, the case number, what happens next, the detail, and the reference date

#### Scenario: One formatter for amounts and dates

- **WHEN** amounts and dates appear on the chips, the transaction panel, and the card
- **THEN** all three use the same locale-aware formatters and the currency code is always visible

#### Scenario: Customer data is never translated

- **WHEN** a merchant name or an amount is rendered
- **THEN** it is shown as stored, because customer data does not pass through the translation files

### Requirement: Always-visible agent button

The customer chat SHALL keep a "talk to an agent" control visible at all times. The first activation SHALL offer help and SHALL NOT hand off. A later activation on the same session SHALL take the handoff path. Traces to REQ-0040 (P0, Pending).

#### Scenario: Agent button escalates

- **WHEN** the customer activates the agent control again on the same session
- **THEN** the chat returns the handoff path

#### Scenario: First agent press offers help

- **WHEN** the customer activates the agent control for the first time
- **THEN** the chat offers help and does not return `handoff`

### Requirement: Customer-facing functional additions

The interface SHALL add a transactions panel where tapping a charge selects exactly that charge, candidate quick-reply chips for clarifications, typing and loading states, a visible reference-date line, and a confirm box before any dispute write. A tap or a chip SHALL NOT open a dispute. Traces to REQ-0038 (P0, Pending) and REQ-0042 (P1, Pending).

#### Scenario: Tapping a charge removes ambiguity

- **WHEN** the customer taps one of the listed charges
- **THEN** the interface selects exactly that transaction and does not open a dispute

#### Scenario: Chip resolves the ambiguity

- **WHEN** the customer taps a candidate chip
- **THEN** the interface continues the conversation with that explicit choice and does not open a dispute

#### Scenario: Ineligible candidate is not selectable

- **WHEN** a candidate is outside the dispute window
- **THEN** its control is disabled and says why, so the customer cannot select it

#### Scenario: Waiting state is visible

- **WHEN** a request is in flight
- **THEN** the interface shows a typing or loading indicator until the reply arrives

#### Scenario: Reference date is on screen

- **WHEN** the interface loads
- **THEN** it shows the reference date the system used for eligibility

#### Scenario: Confirm box uses the brand class

- **WHEN** policy allows a dispute
- **THEN** the interface shows the confirm box and the button sends the candidate id as a structured field
