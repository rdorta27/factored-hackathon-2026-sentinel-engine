# chat-ui Specification

## Purpose

Shows each role an interface where verified outcomes look verified, so the customer trusts the receipt instead of calling to confirm it.

## Requirements

### Requirement: Role-based landing

After login the interface SHALL route each role to its view: chat for customers, queue for advisors, panel for admins. Traces to REQ-0038 (P0, Pending).

#### Scenario: Login lands on the role view

- **WHEN** each mock role signs in
- **THEN** the browser shows chat, queue, or panel respectively

### Requirement: Receipt card with timeline

A `case_confirmation` SHALL render as a receipt card with a verified check, the case facts, and a timeline of completed steps (identity verified, transaction found, rules reviewed, case created, case confirmed). Amounts SHALL show the transaction currency. Traces to REQ-0003 (P0, Pending) and REQ-0041 (P0, Pending).

#### Scenario: Confirmation is visually distinct

- **WHEN** a verified confirmation arrives
- **THEN** the card shows the verified check, all case facts, and the full timeline

### Requirement: Always-visible agent button

The customer chat SHALL keep a "talk to an agent" control visible at all times, triggering the escalation path. Traces to REQ-0040 (P0, Pending).

#### Scenario: Agent button escalates

- **WHEN** the customer activates the agent control
- **THEN** the chat returns the handoff path without requiring further messages

### Requirement: Masked sensitive data

The interface SHALL mask sensitive values (for example card numbers as `****1234`) and SHALL never render full identifiers. Traces to REQ-0047 (P0, Pending).

#### Scenario: No full identifier on screen

- **WHEN** any view renders account or card data
- **THEN** every sensitive value appears masked

### Requirement: Session and denial handling

An expired session SHALL show a re-login notice and return to login; a 403 SHALL show a denied-access message without technical detail. Traces to REQ-0021 (P0, Pending).

#### Scenario: Expired session guides back to login

- **WHEN** an action returns 401 for expiry
- **THEN** the interface shows the re-login notice and routes to login

### Requirement: Themes without session leakage

The interface SHALL support light and dark themes via CSS variables, defaulting to the OS preference with a toggle, and SHALL persist only the theme choice in browser storage, never session data. Traces to REQ-0038 (P0, Pending).

#### Scenario: Theme persists, session does not

- **WHEN** the customer toggles the theme and reloads
- **THEN** the theme persists while no session token exists in browser storage

### Requirement: Locales with fallback

The interface SHALL offer `es-419` as the Spanish base with `es-MX`, `es-CO`, and `es-AR` overriding only changed strings, plus `pt-BR`, from separate translation files with a language selector. A missing regional string SHALL fall back to `es-419`. Traces to REQ-0012 (P0, Pending) and REQ-0044 (P1, Pending).

#### Scenario: Regional fallback works

- **WHEN** `es-AR` lacks a string that `es-419` defines
- **THEN** the interface shows the `es-419` text

#### Scenario: Portuguese is selectable

- **WHEN** the customer selects `pt-BR`
- **THEN** the interface renders the `pt-BR` strings, labeled as team-generated where customer-facing content applies

### Requirement: XSS-safe rendering

The interface SHALL insert all server and customer text via safe text methods, never as executable markup. Traces to REQ-0021 (P0, Pending).

#### Scenario: Markup in text is inert

- **WHEN** any rendered text contains markup characters
- **THEN** the browser displays them literally without executing them
