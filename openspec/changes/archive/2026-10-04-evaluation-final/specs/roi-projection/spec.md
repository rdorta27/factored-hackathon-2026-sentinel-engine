## ADDED Requirements

### Requirement: Inputs are labelled by origin and aggregates hold no rows

The projection SHALL label each input `measured` (frozen run and field), `derived` (computed from the data), `estimated` (team estimate) or `assumed` (replaceable by the reader); the advisor-hour cost SHALL be `assumed`. A script SHALL compute the call-center aggregates (calls, mean handle time with the count of missing durations, first-contact resolution, escalation share) for the transactional reason, write aggregates only to a new write-once folder under `evidence/`, read the data location from the environment, and state that the data does not separate dispute calls from other transactional calls. Traces to REQ-0057 (P1, In progress), REQ-0014 (P0, Done) and REQ-0034 (P0, Done).

#### Scenario: The advisor hour is an assumption

- **WHEN** the inputs are listed
- **THEN** the advisor-hour cost is labelled `assumed` and cites no dataset

#### Scenario: Only aggregates are written

- **WHEN** the script finishes
- **THEN** the evidence holds counts, means and shares and no row or identifier

### Requirement: The projection gives a break-even, not a saving

The projection SHALL give the safe-resolution rate at which the monthly cost of the system equals the human cost it replaces, a sensitivity table over a stated advisor-hour range, and the measured simulated resolution rate beside it with numerator, denominator and label. It SHALL NOT state a measured saving, price an unsafe outcome or claim a saving from better handoffs. Traces to REQ-0057 (P1, In progress), REQ-0055 (P0, In progress) and REQ-0056 (P0, In progress).

#### Scenario: No measured saving is claimed

- **WHEN** the document is read
- **THEN** every figure is labelled a projection or a simulation
