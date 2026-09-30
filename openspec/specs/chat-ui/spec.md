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

A `case_confirmation` SHALL render as a receipt card whose first line states the outcome in plain language, followed by a large case number, then what happens next and when, and finally the detail with the download. Amounts SHALL show the transaction's own currency with its code visible, dates SHALL follow one shared locale-aware format, and the card SHALL state that no funds were held or moved. Traces to REQ-0003 (P0, Pending), REQ-0041 (P0, Pending), and REQ-0004 (P0, Pending).

#### Scenario: Confirmation is visually distinct

- **WHEN** a verified confirmation arrives
- **THEN** the card shows the verified check, the case number, what happens next with its date, the detail, and the download

#### Scenario: One formatter for amounts and dates

- **WHEN** amounts and dates appear on the chips, the transaction panel, and the card
- **THEN** all three use the same locale-aware formatters and the currency code is always visible

#### Scenario: Customer data is never translated

- **WHEN** a merchant name or an amount is rendered
- **THEN** it is shown as stored, because customer data does not pass through the translation files

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

The interface SHALL offer `es-419` as the Spanish base with `es-MX`, `es-CO`, and `es-AR` overriding only changed strings, plus `pt-BR`, from separate translation files with a language selector, starting in the language that matches the customer's country. A missing regional string SHALL fall back to `es-419`. Traces to REQ-0012 (P0, Pending) and REQ-0044 (P1, Pending).

#### Scenario: Regional fallback works

- **WHEN** `es-AR` lacks a string that `es-419` defines
- **THEN** the interface shows the `es-419` text

#### Scenario: Portuguese is selectable

- **WHEN** the customer selects `pt-BR`
- **THEN** the interface renders the `pt-BR` strings, labeled as team-generated where customer-facing content applies

#### Scenario: Default language follows the customer's country

- **WHEN** the demo customer signs in
- **THEN** the interface starts in that customer's country locale and remains switchable

### Requirement: Customer-facing functional additions

The interface SHALL add a transactions panel where tapping a charge starts exactly that dispute, candidate quick-reply chips for clarifications, typing and loading states, and a visible reference-date line. Traces to REQ-0038 (P0, Pending) and REQ-0042 (P1, Pending).

#### Scenario: Tapping a charge removes ambiguity

- **WHEN** the customer taps one of the listed charges
- **THEN** the interface starts the dispute for exactly that transaction

#### Scenario: Chip resolves the ambiguity

- **WHEN** the customer taps a candidate chip
- **THEN** the interface continues the conversation with that explicit choice

#### Scenario: Ineligible candidate is not selectable

- **WHEN** a candidate is outside the dispute window
- **THEN** its control is disabled and says why, so the customer cannot select it

#### Scenario: Waiting state is visible

- **WHEN** a request is in flight
- **THEN** the interface shows a typing or loading indicator until the reply arrives

#### Scenario: Reference date is on screen

- **WHEN** the interface loads
- **THEN** it shows the reference date the system used for eligibility

### Requirement: No internal identifiers on screen

The interface SHALL never display an internal transaction identifier to the customer. Selecting a transaction SHALL send the identifier as a structured request field, and the conversation SHALL show a human-readable description instead. Traces to REQ-0047 (P0, Pending).

#### Scenario: Selection is described, not coded

- **WHEN** the customer selects a transaction
- **THEN** the thread shows the merchant, amount, and date, and the identifier travels only in the request body

### Requirement: Complete localization of visible text

Every visible string SHALL come from the translation files for `es-419`, `es-MX`, `es-CO`, `es-AR`, and `pt-BR`; no raw keys and no untranslated English SHALL reach the screen, and server replies SHALL carry translation keys rather than authored prose. Traces to REQ-0012 (P0, Pending), REQ-0044 (P1, Pending), and REQ-0051 (P0, Pending).

#### Scenario: Missing card string fails the build

- **WHEN** any receipt, handoff, or shell string is absent from a locale file
- **THEN** a test fails naming the locale and the key

#### Scenario: No raw key on screen

- **WHEN** any view renders
- **THEN** no key name such as `hold`, `rule`, or `ref` appears as visible text

### Requirement: XSS-safe rendering

The interface SHALL insert all server and customer text via safe text methods, never as executable markup. Traces to REQ-0021 (P0, Pending).

#### Scenario: Markup in text is inert

- **WHEN** any rendered text contains markup characters
- **THEN** the browser displays them literally without executing them
