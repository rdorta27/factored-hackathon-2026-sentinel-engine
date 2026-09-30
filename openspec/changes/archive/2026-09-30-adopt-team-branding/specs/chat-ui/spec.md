# Spec Delta

## MODIFIED Requirements

### Requirement: Themes without session leakage

The interface SHALL support light and dark themes through the brand variables only, defaulting to the OS preference with a toggle, and SHALL persist only the theme choice in browser storage, never session data. Theme selection SHALL be expressed as `data-theme` on the document element. Traces to REQ-0038 (P0, Pending).

#### Scenario: Theme persists, session does not

- **WHEN** the customer toggles the theme and reloads
- **THEN** the theme persists while no session token exists in browser storage

#### Scenario: Colors come from the brand sheet

- **WHEN** any screen renders in either theme
- **THEN** every color resolves to a brand variable, with no literal color in the application's own sheet

## ADDED Requirements

### Requirement: Brand sheets as the only color and type source

The interface SHALL load the team's brand stylesheets and SHALL take every color, font family, and font size from the variables they define. The application SHALL ship at most one local sheet, and it SHALL be limited to layout and positioning. Traces to REQ-0038 (P0, Pending) and REQ-0051 (P0, Pending).

#### Scenario: Brand stylesheets are served

- **WHEN** the interface loads
- **THEN** the brand base sheet and the brand chat sheet are requested and return 200

#### Scenario: Local sheet stays layout-only

- **WHEN** the application's own sheet is inspected
- **THEN** it declares no color literal and no font family

#### Scenario: Brand folder is never modified

- **WHEN** the change is reviewed
- **THEN** `branding/` shows no modification and the app reads it as-is

### Requirement: Contrast-safe text tokens

The interface SHALL use AA-passing tokens for body text and SHALL NOT use the muted token for small text on light surfaces. Information SHALL never be carried by color alone. Traces to REQ-0038 (P0, Pending).

#### Scenario: Small text uses an AA token

- **WHEN** a label, value, or hint is rendered at body or smaller size
- **THEN** its color is a text token that meets AA against its background

#### Scenario: Status is stated in words

- **WHEN** a status such as verified or escalated is shown
- **THEN** it is accompanied by text, and a color change alone never conveys it

### Requirement: Brand-class receipt and queue surfaces

The verified receipt, the advisor queue cards, and the admin tables SHALL be composed from the classes the brand sheet provides, using the brand's table and callout variables, so all surfaces follow the active theme. Traces to REQ-0041 (P0, Pending) and REQ-0003 (P0, Pending).

#### Scenario: Receipt follows the theme

- **WHEN** the theme switches
- **THEN** the receipt, queue cards, and tables change with it, because they use brand variables rather than fixed values

#### Scenario: Layout adapts without restyling

- **WHEN** the viewport crosses the desktop breakpoint
- **THEN** the transactions panel moves between the second column and the strip above the thread, and only positioning changes
