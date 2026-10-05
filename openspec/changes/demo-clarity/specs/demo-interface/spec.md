## ADDED Requirements

### Requirement: The demo page labels what is simulated

The page SHALL tell the visitor that the data, the login, the advisor and the policy are simulated, in the languages of the page. The example buttons SHALL show only when the demo is available. Traces to REQ-0038 (P0, Done), REQ-0031 (P0, Done) and REQ-0032 (P1, Done).

#### Scenario: Demo available

- **WHEN** the demo is available
- **THEN** the page shows the label "Try an example" and the example buttons
- **AND** the guide lists the three cases and the four simulated parts

#### Scenario: Demo not available

- **WHEN** the demo is not available
- **THEN** the example buttons and their label stay hidden

### Requirement: The page shows which build runs

The page SHALL show the model, the prompt version, the first 8 characters of the `bundle_hash` and the Gold source, read from `GET /api/v1/health`. The read SHALL NOT need a session and SHALL NOT write state. Traces to REQ-0035 (P0, Done).

#### Scenario: Health unavailable

- **WHEN** the health request fails
- **THEN** the build line stays hidden and the chat works as before

### Requirement: The interface change does not break the checks

The change SHALL keep each existing element id, `data-testid` and i18n key. Traces to REQ-0038 (P0, Done).

#### Scenario: Existing checks

- **WHEN** the UI tests, the phone captures at 390 px and `scripts/e2e_check.py` run
- **THEN** they pass

### Requirement: The page handles an account without charges

The page SHALL show a message in the charges panel when the account has no charges. The example buttons and their label SHALL show only when a charge or a repeated merchant exists. The person button SHALL NOT show alone. Traces to REQ-0038 (P0, Done).

#### Scenario: Empty account

- **WHEN** the account has no charges
- **THEN** the charges panel shows the empty message
- **AND** the page hides the example buttons and their label

### Requirement: The claims panel pages a long list

The page SHALL show the five most recent claims and one control for the rest. The API SHALL NOT change. Traces to REQ-0038 (P0, Done).

#### Scenario: More than five claims

- **WHEN** the account has more than five claims
- **THEN** the panel shows five cards and a "Show all" control with the total
- **AND** the control shows every claim
