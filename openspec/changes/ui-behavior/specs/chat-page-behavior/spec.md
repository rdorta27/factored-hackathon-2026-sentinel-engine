## ADDED Requirements

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
