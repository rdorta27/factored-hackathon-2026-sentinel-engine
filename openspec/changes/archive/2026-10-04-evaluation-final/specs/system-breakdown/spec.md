## ADDED Requirements

### Requirement: System outcomes are reported per language and country

Every new system run SHALL report its mandatory outcome metrics for the whole run and for each language variant and each account country present, each with its n. A group whose interval is wider than ±10 points SHALL be labelled descriptive; a group with no attempted case SHALL report its rates as not defined. Group counts SHALL add up to the run totals. Frozen runs SHALL NOT be recomputed. Traces to REQ-0024 (P1, Done), REQ-0055 (P0, In progress) and REQ-0022 (P0, Done).

#### Scenario: Each group carries its n

- **WHEN** a system run is frozen
- **THEN** its summary holds the outcome metrics per variant and per country, each with its n, adding up to the totals

### Requirement: Country monitoring is read from the turn log

A script SHALL aggregate turn records per account country and language: turns, p50 and p95 turn latency, failed or timed-out steps, escalations and handoffs, fallback turns and cost. It SHALL write aggregates only, write-once, state the workload read (source, turns, period) and label a replayed workload as simulated; a country outside MX, CO and AR SHALL be reported apart. Traces to REQ-0050 (P1, Done), REQ-0025 (P1, Done) and REQ-0052 (P0, In progress).

#### Scenario: Monitoring per country

- **WHEN** the script reads records from MX, CO and AR
- **THEN** it reports each country's turns, latency percentiles, failures, escalations, fallbacks and cost, and no trace id, session reference or text

### Requirement: Segment is declared, not invented

While cases and sessions carry no customer segment, reports SHALL say system outcomes are not broken down by segment and why, and SHALL cite dataset segment figures only as dataset context. Traces to REQ-0024 (P1, Done) and REQ-0013 (P0, In progress).

#### Scenario: Segment is explained

- **WHEN** the breakdown is reported
- **THEN** it states that segment is not measured on the current cases
