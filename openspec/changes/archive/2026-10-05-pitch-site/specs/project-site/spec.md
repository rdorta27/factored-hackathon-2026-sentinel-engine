## ADDED Requirements

### Requirement: The project site is static and in English

The repository SHALL contain a static site in `site/`, in English, that describes the product, how it works, the measured results, the demo cases and the links to the live demo and the repository. A workflow SHALL publish `site/` to GitHub Pages from `main`. Traces to REQ-0051 (P0, In progress) and REQ-0056 (P0, In progress).

#### Scenario: Publication

- **WHEN** a change to `site/` merges into `main`
- **THEN** the workflow publishes the site to GitHub Pages

### Requirement: Site numbers come from the evidence

Each number on the site SHALL come from a field of a frozen `summary.json` through `site/numbers.json`, and SHALL show its type: simulation, test suite or projection. A test SHALL fail if a number differs from the evidence. Traces to REQ-0022 (P0, Done) and REQ-0031 (P0, Done).

#### Scenario: A stale number

- **WHEN** a frozen run changes and `site/numbers.json` is not regenerated
- **THEN** the test fails and names the number

### Requirement: The site explains the system with interactive diagrams

The site SHALL offer standalone interactive diagrams of the architecture, one chat turn, the three demo cases and the evidence. Each diagram SHALL work without an external library, with the keyboard and at 390 px. Each number in a diagram SHALL come from `site/numbers.json` and SHALL show its denominator and its type. Traces to REQ-0036 (P0, Pending) and REQ-0056 (P0, In progress).

#### Scenario: Demo and production view

- **WHEN** a visitor switches the architecture diagram to production
- **THEN** each mock shows the component that replaces it

#### Scenario: A number in a diagram

- **WHEN** a diagram shows a metric
- **THEN** it shows the denominator, the type label and the field of the evidence

### Requirement: The site holds no secret

The site SHALL NOT hold a password, a key, a bucket name, an account id or a dataset row. The "Try it" section SHALL say that the credentials are in the submission email. Traces to REQ-0034 (P0, Done) and REQ-0027 (P0, Done).

#### Scenario: Search

- **WHEN** a search runs on `site/`
- **THEN** it finds none of these values

### Requirement: The site is available in three languages with one navigation

The site SHALL be available in English, Spanish (es-419) and Portuguese (pt-BR). Every page SHALL show the same navigation and a language switch that opens the same page in the other language. Each translated number SHALL equal the number of the English page. Traces to REQ-0051 (P0, In progress) and REQ-0012 (P0, Done).

#### Scenario: Language switch

- **WHEN** a visitor selects another language on a page
- **THEN** the same page opens in that language, with the same navigation

#### Scenario: Browser language

- **WHEN** a visitor with no saved choice opens the English home page and the browser language is Spanish or Portuguese
- **THEN** the page opens in that language, and the switch can change it

#### Scenario: A text with no translation

- **WHEN** an English page holds a text that a dictionary does not translate
- **THEN** the build and the tests fail and name the text
