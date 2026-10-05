# chat-page-behavior Specification

## Purpose

Sets how the chat page and the advisor view behave: one turn at a time, the language of the customer, navigation by URL, the handoff as data and the information cards of closed charges.

## Requirements

### Requirement: One click starts one turn

While a turn runs, the page SHALL disable every control that sends a message or picks a charge. A second click SHALL NOT start a second turn. The controls SHALL unlock when the turn ends, fails or times out. Traces to REQ-0038 (P0, Done).

#### Scenario: Double click

- **WHEN** the customer clicks "send" twice
- **THEN** the page sends one turn

#### Scenario: A failed turn

- **WHEN** a turn fails
- **THEN** the controls unlock

### Requirement: The page answers in the language of the customer

The page SHALL redraw the thread after each locale load and SHALL use only the last locale request. The welcome of a persona SHALL show in the language of the persona. Raw i18n keys SHALL stay hidden until the first locale loads. Traces to REQ-0038 (P0, Done).

#### Scenario: Persona welcome

- **WHEN** a persona with another language enters
- **THEN** the welcome shows in that language

### Requirement: Closed turns stay closed

The page SHALL disable the candidate chips of a closed turn. Traces to REQ-0042 (P1, Done).

#### Scenario: An old chip

- **WHEN** a later turn opens
- **THEN** the chips of the earlier turns are disabled

### Requirement: The view lives in the URL

The page SHALL keep the current view in the URL hash: `#/` for the entry, `#/chat`, `#/queue` and `#/queue/<case id>`. A reload with a live session SHALL return to the same view. The Back button SHALL move between views. Traces to REQ-0038 (P0, Done).

#### Scenario: Reload in a case

- **WHEN** an advisor reloads the page at `#/queue/<case id>`
- **THEN** the page shows the same case

### Requirement: The advisor reads the handoff as data

The advisor view SHALL show the list and the open case side by side on a wide screen. The case SHALL have a JSON tab with the ticket and the trace. The JSON SHALL NOT hold `customer_id`. Traces to REQ-0008 (P0, Done).

#### Scenario: JSON tab

- **WHEN** an advisor opens the JSON tab of a case
- **THEN** the page shows the ticket and the trace as JSON
- **AND** the text does not contain `customer_id`

### Requirement: One charge files one ticket

When a charge already has a handoff ticket for the customer, a new handoff on that charge SHALL reuse that ticket, also in a new session. The listing SHALL mark that charge as not eligible. Traces to REQ-0008 (P0, Done).

#### Scenario: A second session

- **WHEN** a customer asks for a person on a charge that has a ticket, in a new session
- **THEN** the reply carries the first reference and the case store holds one ticket for the charge

### Requirement: A closed charge explains itself

A tap on a closed charge or on a claim SHALL open an information card in the thread and SHALL NOT send a chat turn. The card SHALL show the state, the reason and the facts that the server sends. The page SHALL NOT compute a date. Traces to REQ-0038 (P0, Done).

#### Scenario: Outside the window

- **WHEN** a customer taps a charge outside the window
- **THEN** the card shows the window in days and the last day to dispute, as the server sends them
