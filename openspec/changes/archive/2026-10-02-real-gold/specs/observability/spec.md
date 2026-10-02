## ADDED Requirements

### Requirement: The guard covers real customer ids

The record guard SHALL reject the customer-id shapes of both the mock (`CUST-` followed by digits) and the dataset (`CLI-` followed by alphanumerics), in every text field of a record. Traces to REQ-0047 (P0, Done) and REQ-0027 (P0, Done).

#### Scenario: A real id is rejected

- **WHEN** a record would carry a dataset customer id
- **THEN** the record is rejected and nothing is written
