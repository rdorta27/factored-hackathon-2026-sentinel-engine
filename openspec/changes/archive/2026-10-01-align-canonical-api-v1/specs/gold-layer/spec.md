# Spec Delta

## MODIFIED Requirements

### Requirement: Mock labeled, real deferred

The system SHALL read Gold through the `GoldTransactions` seam with two interchangeable adapters: a DuckDB adapter over the PII-free view `v_service_dispute_eligible_transactions`, used when the view answers a probe at startup, and the in-memory mock otherwise. `SENTINEL_GOLD_SOURCE` (`auto`, `mock`, `duckdb`) SHALL select the adapter, and `GET /api/v1/health` SHALL report which one is active. Confirmations SHALL keep `source=mock` while the dispute store is in memory. Traces to REQ-0032 (P1, In progress), REQ-0028 (P0, In progress), and REQ-0015 (P0, In progress).

#### Scenario: Mock source is visible

- **WHEN** any confirmation is produced with the in-memory dispute store
- **THEN** its source field reads `mock`

#### Scenario: Missing view falls back to the mock

- **WHEN** the Gold view is absent or DuckDB cannot read it
- **THEN** the app starts on the mock and the health route reports `mock`

### Requirement: Session listing endpoint

The app SHALL expose `GET /api/v1/transactions` for the signed-in customer. The response SHALL contain only that customer's rows, ordered by date, and the as-of mark; each row SHALL have the same shape as a chat candidate: reference, date, amount, currency, merchant, status, `eligible`, and `ineligibleKey`. The request SHALL NOT accept a customer identifier. A row belonging to another customer SHALL NOT appear. The read-seam operations that take a customer identifier SHALL keep those signatures. Traces to REQ-0042 (P1, In progress), REQ-0032 (P1, In progress), REQ-0039 (P0, In progress), and REQ-0047 (P0, In progress).

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
