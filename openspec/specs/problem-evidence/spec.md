# problem-evidence Specification

## Purpose
Define the evidence for the size of the problem. A frozen run reports the call numbers for the development zone only. A page explains these numbers in plain words. Each rate shows its count and its range.

## Requirements

### Requirement: The problem numbers come from a frozen run

The repository SHALL hold a frozen run that reports, for the development zone only: the share of calls solved at the first contact by reason for the call, the calls per day by workflow (average, busy-day level and highest day), the agent hours per month of each candidate workflow with their ranking, and the share of missing values in the fields used. Each rate SHALL show its count and a 95% range. The mapping from reasons to workflows SHALL be committed before the first number. The run SHALL write totals only. Traces to REQ-0014 (P0, Done), REQ-0053 (P0, Done) and REQ-0013 (P0, In progress).

#### Scenario: A rate has its count and its range

- **WHEN** the run reports the first-contact rate of a reason
- **THEN** the summary holds the number of calls, the number solved and a 95% range

#### Scenario: Held-out data is not read

- **WHEN** the run reads the call table
- **THEN** it excludes every event dated 2025-07-01 or later and reports how many it excluded

#### Scenario: Missing handling time is counted

- **WHEN** some calls have no duration
- **THEN** the summary reports how many, and the agent hours use only the calls with a duration

### Requirement: The page explains the numbers in plain words

The page `docs/rationale/problem-and-demand.md` SHALL define each measure in plain words, SHALL cite the field of each number, and SHALL state that the dataset is synthetic and that the saving range is an offline projection. Traces to REQ-0013 (P0, In progress) and REQ-0031 (P0, Done).

#### Scenario: The page names its limits

- **WHEN** a reader looks for what the data cannot say
- **THEN** the page lists the missing link between complaints and transactions and the missing product field
