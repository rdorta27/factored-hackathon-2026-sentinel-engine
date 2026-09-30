# gold-layer Specification

## Purpose

Gives the backend one read seam for transaction eligibility that serves invented mock rows today and DuckDB or Delta Lake rows tomorrow without changing callers.

## Requirements

### Requirement: Denormalized Gold read seam

The system SHALL read transaction eligibility through a single seam returning denormalized rows with transaction date, status, refunded and prior-dispute flags, and an as-of freshness mark. Every read SHALL return its as-of mark alongside the data. Traces to REQ-0039 (P0, Pending) and REQ-0032 (P1, Pending).

#### Scenario: Eligibility read carries freshness

- **WHEN** the disputes service checks a transaction
- **THEN** the row includes the as-of mark that the confirmation can display

#### Scenario: Unknown transaction is not eligible

- **WHEN** the reference matches no Gold row for the session customer
- **THEN** the system treats it as ineligible and offers a handoff

### Requirement: Mock labeled, real deferred

Phase 1 SHALL serve invented rows from an in-memory mock labeled `source=mock`; the DuckDB and Delta Lake adapters SHALL remain a documented later swap with unchanged contracts. Traces to REQ-0032 (P1, Pending) and REQ-0028 (P0, Pending).

#### Scenario: Mock source is visible

- **WHEN** any confirmation is produced in Phase 1
- **THEN** its source field reads `mock`

### Requirement: Per-customer isolation on reads

Gold reads SHALL filter by the session customer; a customer SHALL never see another customer's rows. Traces to REQ-0007 (P0, Pending) and REQ-0047 (P0, Pending).

#### Scenario: Cross-customer reference is invisible

- **WHEN** a customer references another customer's transaction
- **THEN** the lookup behaves as unknown and offers a handoff

### Requirement: Per-country demo customers

The Gold mock SHALL provide coherent customers for Mexico, Colombia, and Argentina, each with transactions denominated in that country's currency and dated relative to the configured reference date. Traces to REQ-0041 (P0, Pending), REQ-0049 (P2, Pending), and REQ-0032 (P1, Pending).

#### Scenario: Each country reads its own currency

- **WHEN** the CO customer lists transactions
- **THEN** every row is denominated in COP, and the MX and AR customers read MXN and ARS respectively

#### Scenario: Merchant lookup is country-neutral

- **WHEN** the customer lists candidate transactions
- **THEN** each candidate carries date, amount, currency, and merchant for the interface to display

### Requirement: Transaction listing for the interface

The seam SHALL support listing every transaction of one session customer, ordered by date, so the interface can show the transaction panel and offer candidates. Traces to REQ-0042 (P1, Pending) and REQ-0003 (P0, Pending).

#### Scenario: Listing stays inside the session customer

- **WHEN** a customer requests their transactions
- **THEN** the response contains only their own rows

### Requirement: Session listing endpoint

The submission app SHALL expose `GET /transactions` for the signed-in customer. The response SHALL contain only that customer's rows, ordered by date, each with date, amount, currency, merchant, status, and the as-of mark. The request SHALL NOT accept a customer identifier. A row belonging to another customer SHALL NOT appear. The read-seam operations that take a customer identifier SHALL keep those signatures. Traces to REQ-0042 (P1, Pending), REQ-0032 (P1, Pending), REQ-0039 (P0, Pending), and REQ-0047 (P0, Pending).

#### Scenario: Listing stays inside the session

- **WHEN** a customer requests `GET /transactions`
- **THEN** the response contains only their own rows and the as-of mark

#### Scenario: Another customer's row is absent

- **WHEN** customer A lists transactions and customer B has rows
- **THEN** customer B's references are not in the response

#### Scenario: No customer identifier in the query

- **WHEN** the listing request includes a customer identifier
- **THEN** the system rejects the request and does not use that identifier to choose rows
