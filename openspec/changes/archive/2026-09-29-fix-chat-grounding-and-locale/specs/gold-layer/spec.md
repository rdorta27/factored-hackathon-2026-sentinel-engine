# Spec Delta

## MODIFIED Requirements

### Requirement: Denormalized Gold read seam

The system SHALL read transaction eligibility through a single seam returning denormalized rows with transaction date, status, refunded and prior-dispute flags, and an as-of freshness mark. Every read SHALL return its as-of mark alongside the data. Traces to REQ-0039 (P0, Pending) and REQ-0032 (P1, Pending).

#### Scenario: Eligibility read carries freshness

- **WHEN** the disputes service checks a transaction
- **THEN** the row includes the as-of mark that the confirmation can display

#### Scenario: Unknown transaction is not eligible

- **WHEN** the reference matches no Gold row for the session customer
- **THEN** the system treats it as ineligible and offers a handoff

## ADDED Requirements

### Requirement: Per-country demo customers

The Gold mock SHALL provide coherent customers for Mexico, Colombia, and Argentina, each with transactions denominated in that country's currency and dated relative to the configured reference date. Traces to REQ-0041 (P0, Pending), REQ-0049 (P2, Pending), and REQ-0032 (P1, Pending).

#### Scenario: Each country reads its own currency

- **WHEN** the co customer lists transactions
- **THEN** every row is denominated in COP, and the mx and ar customers read MXN and ARS respectively

#### Scenario: Merchant lookup is country-neutral

- **WHEN** the customer lists candidate transactions
- **THEN** each candidate carries date, amount, currency, and merchant for the interface to display

### Requirement: Transaction listing for the interface

The seam SHALL support listing every transaction of one session customer, ordered by date, so the interface can show the transaction panel and offer candidates. Traces to REQ-0042 (P1, Pending) and REQ-0003 (P0, Pending).

#### Scenario: Listing stays inside the session customer

- **WHEN** a customer requests their transactions
- **THEN** the response contains only their own rows
