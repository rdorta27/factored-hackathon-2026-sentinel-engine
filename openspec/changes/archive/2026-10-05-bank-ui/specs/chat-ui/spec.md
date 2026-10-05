## ADDED Requirements

### Requirement: Each recent charge shows its case state

The recent-charges panel SHALL show a state for each charge from the server: eligible, in review, with an advisor, already disputed, outside the window, or not disputable. The page SHALL NOT compute the state. Traces to REQ-0038 (P0, Done) and REQ-0043 (P1, Done).

#### Scenario: Charge with an open dispute

- **WHEN** a charge has an open dispute
- **THEN** the panel shows it as already disputed

### Requirement: The page shows a bank shell without balances

The header SHALL show the configured bank name, the product type and last four digits of the session product, the country, the language and the as-of date. It SHALL NOT show a balance. Traces to REQ-0038 (P0, Done) and REQ-0039 (P0, Done).

#### Scenario: Header of a customer session

- **WHEN** a customer logs in
- **THEN** the header shows the masked product and the as-of date, and no balance

### Requirement: The brand is configuration

`SENTINEL_BRAND_NAME` and `SENTINEL_BRAND_ACCENT` SHALL set the bank name and the accent color. An accent that fails the contrast check SHALL fall back to the default. Traces to REQ-0049 (P2, Done).

#### Scenario: Another bank

- **WHEN** the service starts with another name and a valid accent
- **THEN** the page shows that name and color

### Requirement: The thread works on a phone

At 390 px wide, the thread SHALL fill the screen, the side panels SHALL open from a button, and every control SHALL be at least 44 px high. Traces to REQ-0038 (P0, Done).

#### Scenario: Phone width

- **WHEN** the page is 390 px wide
- **THEN** no horizontal scroll appears and the side panels open from a button

## MODIFIED Requirements

### Requirement: The interface carries the product identity

The interface SHALL show the Sentinel product mark and the line stating its purpose, load fonts and assets only from `branding/`, use the bank accent color for actions and the user's messages, use a success color distinct from the accent for verified states, and keep a text label on every status color. The Sentinel violet and rose SHALL appear only in the product mark. Traces to REQ-0038 (P0, Done).

#### Scenario: No external font request

- **WHEN** the page loads
- **THEN** no font or asset is requested from outside the app

#### Scenario: Bank accent, Sentinel mark

- **WHEN** the page shows a button and the product mark
- **THEN** the button uses the bank accent and the mark keeps the Sentinel colors
