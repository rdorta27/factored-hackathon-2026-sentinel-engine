# gold-layer Specification

## Purpose

Gives the backend one read seam for transaction eligibility that serves invented mock rows today and DuckDB or Delta Lake rows tomorrow without changing callers.

## Requirements

### Requirement: Denormalized Gold read seam

The system SHALL read transaction eligibility through a single seam returning denormalized rows with transaction date, status, refunded and prior-dispute flags, and an as-of freshness mark. Every read SHALL return its as-of mark alongside the data. Traces to REQ-0039 (P0, Done) and REQ-0032 (P1, Done).

#### Scenario: Eligibility read carries freshness

- **WHEN** the disputes service checks a transaction
- **THEN** the row includes the as-of mark that the confirmation can display

#### Scenario: Unknown transaction is not eligible

- **WHEN** the reference matches no Gold row for the session customer
- **THEN** the system treats it as ineligible and offers a handoff

### Requirement: Mock labeled, real deferred

The system SHALL read Gold through the `GoldTransactions` seam with two interchangeable adapters: a DuckDB adapter over the PII-free view `v_service_dispute_eligible_transactions`, used when the view answers a probe at startup, and the in-memory mock otherwise. `SENTINEL_GOLD_SOURCE` (`auto`, `mock`, `duckdb`) SHALL select the adapter, and `GET /api/v1/health` SHALL report which one is active. Confirmations SHALL keep `source=mock` while the dispute store is in memory. Traces to REQ-0032 (P1, Done), REQ-0028 (P0, Done), and REQ-0015 (P0, Done).

#### Scenario: Mock source is visible

- **WHEN** any confirmation is produced with the in-memory dispute store
- **THEN** its source field reads `mock`

#### Scenario: Missing view falls back to the mock

- **WHEN** the Gold view is absent or DuckDB cannot read it
- **THEN** the app starts on the mock and the health route reports `mock`

### Requirement: Per-customer isolation on reads

Gold reads SHALL filter by the session customer; a customer SHALL never see another customer's rows. Traces to REQ-0007 (P0, Done) and REQ-0047 (P0, Done).

#### Scenario: Cross-customer reference is invisible

- **WHEN** a customer references another customer's transaction
- **THEN** the lookup behaves as unknown and offers a handoff

### Requirement: Per-country demo customers

The Gold mock SHALL provide coherent customers for Mexico, Colombia, and Argentina, the only account countries in the dataset (data dictionary, `customers.country`). Each customer's transactions SHALL be denominated in the currency of the product they belong to: the country's local currency, or USD for a USD product. Rows SHALL be dated relative to the configured reference date. For each demo country, the mock SHALL include at least one charge above each configured fraud-score threshold and one above each configured high-amount threshold, so every rule can be shown. Traces to REQ-0041 (P0, Done), REQ-0049 (P2, Done), REQ-0032 (P1, Done) and REQ-0006 (P0, Done).

#### Scenario: Each country reads its own currency

- **WHEN** the CO customer lists transactions
- **THEN** every row is denominated in COP or USD, and the MX and AR customers read MXN or USD and ARS or USD respectively

#### Scenario: Merchant lookup is country-neutral

- **WHEN** the customer lists candidate transactions
- **THEN** each candidate carries date, amount, currency, and merchant for the interface to display

#### Scenario: Every configured rule has a demo row

- **WHEN** a fraud-score or high-amount value is configured for a country and currency
- **THEN** the mock holds a charge of that country and currency above it

### Requirement: Transaction listing for the interface

The seam SHALL support listing every transaction of one session customer, ordered by date, so the interface can show the transaction panel and offer candidates. Traces to REQ-0042 (P1, Done) and REQ-0003 (P0, Done).

#### Scenario: Listing stays inside the session customer

- **WHEN** a customer requests their transactions
- **THEN** the response contains only their own rows

### Requirement: Session listing endpoint

The app SHALL expose `GET /api/v1/transactions` for the signed-in customer. The response SHALL contain only that customer's rows, ordered by date, and the as-of mark; each row SHALL have the same shape as a chat candidate: reference, date, amount, currency, merchant, status, `eligible`, and `ineligibleKey`. The request SHALL NOT accept a customer identifier. A row belonging to another customer SHALL NOT appear. The read-seam operations that take a customer identifier SHALL keep those signatures. Traces to REQ-0042 (P1, Done), REQ-0032 (P1, Done), REQ-0039 (P0, Done), and REQ-0047 (P0, Done).

#### Scenario: Listing stays inside the session

- **WHEN** a customer requests `GET /api/v1/transactions`
- **THEN** the response contains only their own rows and the as-of mark

#### Scenario: Another customer's row is absent

- **WHEN** customer A lists transactions and customer B has rows
- **THEN** customer B's references are not in the response

#### Scenario: No customer identifier in the query

- **WHEN** the listing request includes a customer identifier
- **THEN** the system rejects the request and does not use that identifier to choose rows

#### Scenario: Ineligible rows say why

- **WHEN** a row is outside the window, reversed, declined, pending, or already disputed
- **THEN** it has `eligible=false` and a translated `ineligibleKey`

### Requirement: Rows carry the fraud score

Every Gold row SHALL carry the transaction's `fraud_score` (or empty when the source has none) from both the mock and the DuckDB source, and the candidate the policy engine reads SHALL carry it unchanged. The score SHALL NOT be shown to the customer or sent to the model. `is_fraud` SHALL NOT be read, since it is a label known only after investigation. Traces to REQ-0006 (P0, Done), REQ-0047 (P0, Done) and REQ-0017 (P0, Done).

#### Scenario: Score reaches the engine

- **WHEN** a charge above the fraud threshold is selected
- **THEN** the engine receives its score and cites `fraud.score`

#### Scenario: Score stays internal

- **WHEN** the customer lists transactions or receives a reply
- **THEN** no fraud score appears in the response

### Requirement: The Gold file is chosen explicitly

The DuckDB Gold file SHALL be taken from `SENTINEL_GOLD_DUCKDB` when set, otherwise from one path fixed relative to the repository, and SHALL NOT depend on the folder the process was started from. When `SENTINEL_GOLD_SOURCE` is `mock`, no file SHALL be read. The chosen source SHALL be reported by `GET /api/v1/health`. Traces to REQ-0015 (P0, Done), REQ-0028 (P0, Done) and REQ-0032 (P1, Done).

#### Scenario: Same result from any folder

- **WHEN** the app starts from the repository root and from `sentinel-ai-core/` with the same settings
- **THEN** both report the same Gold source

#### Scenario: Mock is honoured

- **WHEN** `SENTINEL_GOLD_SOURCE` is `mock` and the file exists
- **THEN** the app reports `mock` and reads no file

### Requirement: Real rows are limited to the reference date

The DuckDB adapter SHALL NOT return a row dated after the configured reference date, and SHALL filter by the session customer in the query. Traces to REQ-0039 (P0, Done) and REQ-0007 (P0, Done).

#### Scenario: A future-dated row is not listed

- **WHEN** a customer has a row dated after the reference date
- **THEN** it does not appear and cannot be selected

### Requirement: Local users for real customers stay out of the repository

The repository SHALL provide a script that writes a users file for real Gold customers (login, customer id, country, role, salted password hash) to a path ignored by git, choosing customers with a recent approved charge per country and customers that trigger each handoff rule. The script SHALL print counts only and SHALL NOT write identifiers, rows or the data location to any tracked file. Traces to REQ-0034 (P0, Done), REQ-0009 (P0, Done) and REQ-0031 (P0, Done).

#### Scenario: Counts only

- **WHEN** the script finishes
- **THEN** it prints how many users it wrote per country and no identifier

#### Scenario: Output is ignored by git

- **WHEN** the output path is checked
- **THEN** git ignores it

### Requirement: Real-data evidence has no rows

Evidence of a run on real Gold SHALL contain only the source label and outcomes per scenario and language, never a row, a customer id, a transaction id or the data location. Traces to REQ-0034 (P0, Done) and REQ-0009 (P0, Done).

#### Scenario: Evidence holds no identifiers

- **WHEN** the recorded evidence is searched
- **THEN** it contains no customer id, transaction id or data path
