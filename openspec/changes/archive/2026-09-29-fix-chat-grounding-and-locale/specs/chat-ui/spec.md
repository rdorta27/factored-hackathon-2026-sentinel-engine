# Spec Delta

## MODIFIED Requirements

### Requirement: Receipt card with timeline

A `case_confirmation` SHALL render as a receipt card whose first line states the outcome in plain language, followed by a large copyable case number, then what happens next and when, and finally the detail with the download. Amounts SHALL show the transaction's own currency, dates SHALL follow the interface language, and the card SHALL state that no funds were held or moved. Traces to REQ-0003 (P0, Pending), REQ-0041 (P0, Pending), and REQ-0004 (P0, Pending).

#### Scenario: Confirmation is visually distinct

- **WHEN** a verified confirmation arrives
- **THEN** the card shows the human-language outcome, the case number, what happens next with its timing, the detail, and the download

#### Scenario: No unformatted or untranslated text

- **WHEN** any card field is rendered
- **THEN** every label comes from the translation files and every date is formatted for the active language

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

## ADDED Requirements

### Requirement: Customer-facing functional additions

The interface SHALL add, without restyling it: a transactions panel listing the customer's recent charges where tapping one starts that dispute, candidate quick-reply chips for clarifications, typing and loading states, and a visible reference-date line. Visual design and brand tokens belong to the team's `branding/` folder and a later change. Traces to REQ-0038 (P0, Pending) and REQ-0042 (P1, Pending).

#### Scenario: Tapping a charge removes ambiguity

- **WHEN** the customer taps one of the listed charges
- **THEN** the interface starts the dispute for exactly that transaction

#### Scenario: Chip resolves the ambiguity

- **WHEN** the customer taps a candidate chip
- **THEN** the interface continues the conversation with that explicit choice

#### Scenario: Waiting state is visible

- **WHEN** a request is in flight
- **THEN** the interface shows a typing or loading indicator until the reply arrives

#### Scenario: Reference date is on screen

- **WHEN** the interface loads
- **THEN** it shows the reference date the system used for eligibility

### Requirement: Complete localization of visible text

Every visible string SHALL come from the translation files for `es-419`, `es-MX`, `es-CO`, `es-AR`, and `pt-BR`; no raw keys and no untranslated English SHALL reach the screen. Traces to REQ-0012 (P0, Pending), REQ-0044 (P1, Pending), and REQ-0051 (P0, Pending).

#### Scenario: Missing card string fails the build

- **WHEN** any receipt, handoff, or shell string is absent from a locale file
- **THEN** a test fails naming the locale and the key

#### Scenario: No raw key on screen

- **WHEN** any view renders
- **THEN** no key name such as `hold`, `rule`, or `ref` appears as visible text
