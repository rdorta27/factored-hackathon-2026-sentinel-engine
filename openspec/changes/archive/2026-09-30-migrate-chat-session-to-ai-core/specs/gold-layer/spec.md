# Spec Delta

## ADDED Requirements

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
