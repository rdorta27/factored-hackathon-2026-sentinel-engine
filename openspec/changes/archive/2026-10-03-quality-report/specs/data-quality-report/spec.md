## ADDED Requirements

### Requirement: The quality report is generated in full

Every pipeline run that writes the quality report SHALL generate all its sections from the data: per-table Bronze and Silver counts with the drop broken down into deduplication, quarantine per rule and orphans; late arrivals per partitioned table; null counts and rates for mandatory and optional fields; country normalisation counts; Gold eligibility; and the PII guardrails. No section SHALL depend on text added by hand to the generated file. Traces to REQ-0015 (P0, Done) and REQ-0018 (P0, Done).

#### Scenario: A rerun keeps every section

- **WHEN** the pipeline runs with the default report path
- **THEN** the report still contains the volume drop, deduplication, quarantine, orphan, late-arrival and null sections

#### Scenario: Optional nulls are visible

- **WHEN** an optional column has missing values
- **THEN** the report gives its null count and rate

### Requirement: The report can be verified

A `verify` mode SHALL recompute the report figures from the local DuckDB file and SHALL fail when a figure differs from the committed report, naming the figure. It SHALL print aggregates only. Traces to REQ-0015 (P0, Done) and REQ-0028 (P0, Done).

#### Scenario: A stale report is detected

- **WHEN** the committed report differs from a recomputation
- **THEN** `verify` fails and names the differing figure
