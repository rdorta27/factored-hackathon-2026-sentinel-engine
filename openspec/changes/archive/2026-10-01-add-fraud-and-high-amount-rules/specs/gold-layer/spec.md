## MODIFIED Requirements

### Requirement: Per-country demo customers

The Gold mock SHALL provide coherent customers for Mexico, Colombia, and Argentina, the only account countries in the dataset (data dictionary, `customers.country`). Each customer's transactions SHALL be denominated in the currency of the product they belong to: the country's local currency, or USD for a USD product. Rows SHALL be dated relative to the configured reference date. For each demo country, the mock SHALL include at least one charge above each configured fraud-score threshold and one above each configured high-amount threshold, so every rule can be shown. Traces to REQ-0041 (P0, Done), REQ-0049 (P2, Done), REQ-0032 (P1, Done) and REQ-0006 (P0, In progress).

#### Scenario: Each country reads its own currency

- **WHEN** the CO customer lists transactions
- **THEN** every row is denominated in COP or USD, and the MX and AR customers read MXN or USD and ARS or USD respectively

#### Scenario: Merchant lookup is country-neutral

- **WHEN** the customer lists candidate transactions
- **THEN** each candidate carries date, amount, currency, and merchant for the interface to display

#### Scenario: Every configured rule has a demo row

- **WHEN** a fraud-score or high-amount value is configured for a country and currency
- **THEN** the mock holds a charge of that country and currency above it

## ADDED Requirements

### Requirement: Rows carry the fraud score

Every Gold row SHALL carry the transaction's `fraud_score` (or empty when the source has none) from both the mock and the DuckDB source, and the candidate the policy engine reads SHALL carry it unchanged. The score SHALL NOT be shown to the customer or sent to the model. `is_fraud` SHALL NOT be read, since it is a label known only after investigation. Traces to REQ-0006 (P0, In progress), REQ-0047 (P0, In progress) and REQ-0017 (P0, In progress).

#### Scenario: Score reaches the engine

- **WHEN** a charge above the fraud threshold is selected
- **THEN** the engine receives its score and cites `fraud.score`

#### Scenario: Score stays internal

- **WHEN** the customer lists transactions or receives a reply
- **THEN** no fraud score appears in the response
