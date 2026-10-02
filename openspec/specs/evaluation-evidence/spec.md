# evaluation-evidence Specification

## Purpose

Freezes the label universe, the case mix and the reference thresholds of the
bank dataset as reproducible aggregate evidence that the evaluation consumes.

## Requirements

### Requirement: Frozen label universe

The run SHALL persist every `category` and `subcategory` combination for
`case_type = Claim` with its count and share, and SHALL persist the same for
`case_type = Complaint` and for the whole history as the global taxonomy. The
persisted set SHALL be the full counter, never a truncated top list. Traces to
REQ-0016 (P0, Pending) and decision 007.

#### Scenario: The full counter is persisted

- **WHEN** the label universe is written
- **THEN** every distinct combination appears with its count, not only the most frequent ones

#### Scenario: Empty subcategories are reported

- **WHEN** a claim carries no subcategory
- **THEN** the run reports the null count instead of dropping the row silently

### Requirement: Case mix and stratification frame

The run SHALL persist the Claim counts by month, country, reception channel,
priority and status, and the claimed-amount percentiles per subcategory, so the
evaluation set can be stratified to the real distribution. Traces to REQ-0020
(P0, Pending) and REQ-0024 (P1, Pending).

#### Scenario: Mix is available per dimension

- **WHEN** the case mix is written
- **THEN** each dimension (month, country, channel, priority, status) has its own counts

#### Scenario: Amount percentiles are reported

- **WHEN** claimed amounts are summarized
- **THEN** the run reports percentiles per subcategory with the currency, never a single average

### Requirement: Intent mix and automation reference

The run SHALL persist the `contact_reason` distribution and the escalation and
resolution flags for the window, as the reference for the router case mix and
the automation baseline. Traces to REQ-0016 (P0, Pending) and REQ-0055 (P0,
Pending).

#### Scenario: Contact reasons are counted in full

- **WHEN** the intent mix is written
- **THEN** every `contact_reason` value appears with its count

#### Scenario: Automation flags are reported

- **WHEN** the reference is written
- **THEN** the escalation, resolution and follow-up flags are reported as counts with their denominator

### Requirement: Reference thresholds

The run SHALL persist transaction-amount and fraud-score percentiles grouped by the customer's account country (from `customers.country`) and the charge currency, never by `transaction_country` alone and never pooling amounts of different currencies. Country names SHALL be normalized to `México`, `Colombia` and `Argentina` before grouping. The run SHALL also persist the share of products per account country and currency, with its denominator. Traces to REQ-0006 (P0, In progress), REQ-0016 (P0, In progress) and REQ-0015 (P0, In progress); decisions 25 and 26.

#### Scenario: Thresholds are grounded in data

- **WHEN** the thresholds section is written
- **THEN** it reports the amount and fraud-score percentiles per account country and charge currency, each with its count

#### Scenario: Currencies are never pooled

- **WHEN** an account country has charges in its local currency and in USD
- **THEN** the run reports two separate groups and no percentile mixes both

#### Scenario: Country spelling variants collapse

- **WHEN** the source carries both `Mexico` and `México`
- **THEN** both are counted under `México` and the run reports how many rows were normalized

### Requirement: Aggregates only, no personal data

No output of the run SHALL contain dataset rows, `customer_id`, names, documents
or any personal data. Only counts, shares and percentile values SHALL be
written. Traces to REQ-0047 (P0, In progress) and REQ-0031 (P0, Pending).

#### Scenario: No row leaves the process

- **WHEN** a run finishes
- **THEN** every written value is an aggregate and no personal-data field appears

### Requirement: Write-once and reproducible

A run SHALL write to a new `evidence/evaluation/<run-id>/` folder and SHALL never
edit a committed run. A `verify` mode SHALL recompute the data hashes and every
summary field and SHALL fail on any mismatch. Traces to REQ-0028 (P0, Pending).

#### Scenario: A new run gets a new folder

- **WHEN** the script runs again
- **THEN** it writes a new run-id folder without touching earlier runs

#### Scenario: Verify fails on drift

- **WHEN** `verify` recomputes a different hash or value
- **THEN** it exits non-zero and names the mismatch

### Requirement: Development window only

The run SHALL read only the development zone and SHALL NOT read data at or after
the held-out cut, and it SHALL report the held-out row count as zero. Traces to
REQ-0017 (P0, In progress).

#### Scenario: Held-out rows are not read

- **WHEN** the window is applied
- **THEN** rows dated at or after the held-out cut are excluded and the held-out count is reported as zero

### Requirement: Derived label set with provenance

The evaluation runner SHALL consume a derived label set that records the run id
and the summary hash it came from, so a measured result is tied to one frozen
run. Traces to REQ-0016 (P0, Pending) and REQ-0017 (P0, In progress).

#### Scenario: The label set names its source

- **WHEN** the label set is derived
- **THEN** it records the run id and the summary hash it was built from

#### Scenario: A changed run is a new label set

- **WHEN** the frozen run changes
- **THEN** the derived label set changes with it instead of being reused silently
