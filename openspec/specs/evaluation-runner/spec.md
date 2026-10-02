# evaluation-runner Specification

## Purpose

Replays a labelled, versioned conversation set against the model router and the
running system and computes the component and outcome metrics the brief
requires, frozen as reproducible evidence.

## Requirements

### Requirement: Versioned labelled case set

The harness SHALL read a versioned case set in JSON lines where each case
carries an id, locale (`es-419` or `pt-BR`), country (`MX`, `CO` or `AR`), the
customer turns, component labels (`expected_intent`, and `expected_category`
where a dispute applies), system labels (`expected_outcome`, `requires_handoff`),
a tag set (`edge`, `adversarial`) and a split (`development` or `held_out`). The
text SHALL be team-written and declared as simulation, never a dataset row.
Traces to REQ-0017 (P0, In progress) and REQ-0031 (P0, Pending).

#### Scenario: Every case is fully labelled

- **WHEN** the case set is loaded
- **THEN** each case has an id, a locale, a country, its turns and both label groups

#### Scenario: No dataset row is used as a case

- **WHEN** a case is authored
- **THEN** its text is team-written and no dataset row is copied into the set

### Requirement: Component benchmark over the four pillars

The harness SHALL run the model port directly over the case set and compute:
intent accuracy and per-class precision, recall and F1 by locale; a safety pass
rate over the cases that must not pass; an automation proxy; and stability as
the agreement across repeated runs. Traces to REQ-0016 (P0, Pending) and
REQ-0020 (P0, Pending).

#### Scenario: Intent metrics per class and locale

- **WHEN** the component benchmark finishes
- **THEN** it reports accuracy and per-class precision, recall and F1 for each locale

#### Scenario: Safety pass rate counts what must not pass

- **WHEN** a case is tagged as one that must not pass
- **THEN** the safety pass rate counts it and names it on failure

#### Scenario: Stability repeats the same input

- **WHEN** a case is run N times
- **THEN** the harness reports the agreement across the runs

### Requirement: Baseline and system on the same held-out set

The harness SHALL run the prompted router and the keyword baseline over the same
cases on the same split, so a result compares like with like, and the held-out
split SHALL be measured once. Traces to REQ-0020 (P0, Pending) and REQ-0017 (P0,
In progress).

#### Scenario: Both models see the same cases

- **WHEN** the comparison is produced
- **THEN** both the router and the baseline were run on the identical case set

#### Scenario: A case never appears in both splits

- **WHEN** the splits are applied
- **THEN** no case id appears in both the development and the held-out split

### Requirement: System runner replays the loop and reads the logs

The harness SHALL replay each case against `POST /api/v1/chat` with a test session,
inject the declared faults (Gold unavailable, expired session, tool failure), and
recover the turn's records by `trace_id`. Traces to REQ-0025 (P1, In progress)
and REQ-0021 (P0, Done).

#### Scenario: A case is replayed end to end

- **WHEN** a case is run through the system
- **THEN** the turn completes and its outcome is compared with the expected label

#### Scenario: An injected fault is handled and recorded

- **WHEN** a declared fault is injected
- **THEN** the turn degrades safely and the fault appears in the records

#### Scenario: Records are read by trace id

- **WHEN** a turn finishes
- **THEN** the harness reads every record of that turn by its `trace_id`

### Requirement: Mandatory outcome metrics

The harness SHALL compute safe automated resolution with the share where
automation was attempted, containment, escalation quality (missed and
unnecessary transfers), unsafe outcomes with counts and denominators, p50 and
p95 latency, and cost per attempted case and per successful resolution
("not defined" when there are none). Traces to REQ-0055 (P0, Pending) and
REQ-0057 (P1, Pending).

#### Scenario: Every mandatory metric is present

- **WHEN** the system run finishes
- **THEN** the report carries every mandatory metric with its denominator

#### Scenario: Cost per resolution is not defined when there are none

- **WHEN** no case is resolved
- **THEN** cost per successful resolution is reported as not defined, never as zero

### Requirement: Every result carries n, mix, versions and variability

Each reported metric SHALL carry its sample size, the case mix, the model and
prompt versions and the variability across runs, and the report SHALL list the
failures, not only the successes. Traces to REQ-0022 (P0, Pending), REQ-0019
(P1, Pending) and REQ-0024 (P1, Pending).

#### Scenario: A metric without n is not reported

- **WHEN** a metric is written
- **THEN** it carries its sample size and the case mix

#### Scenario: Failures appear in the report

- **WHEN** a case fails
- **THEN** the report lists it with its count and reason

### Requirement: Reproducible offline

The harness SHALL run without network access using recorded responses, and the
same case set SHALL produce the same result on a re-run. Traces to REQ-0028 (P0,
Pending).

#### Scenario: The runner opens no connection

- **WHEN** a run is executed
- **THEN** no network connection is opened

#### Scenario: A re-run reproduces the result

- **WHEN** the same case set is run again
- **THEN** the summary matches the earlier run

### Requirement: Write-once frozen results

A run SHALL write one new `evidence/evaluation-runs/<run-id>/summary.json` and
SHALL never edit a committed run; the report SHALL cite `summary.json` fields.
Traces to REQ-0028 (P0, Pending).

#### Scenario: A new run gets a new folder

- **WHEN** the harness runs again
- **THEN** it writes a new run-id folder without touching earlier runs

#### Scenario: A committed run is never overwritten

- **WHEN** a run id already exists
- **THEN** the harness refuses to overwrite it

### Requirement: Label set provenance

The harness SHALL consume the pinned label set and SHALL record with its results
the run id and the hash of the label set it used. Traces to REQ-0016 (P0,
Pending) and REQ-0017 (P0, In progress).

#### Scenario: The result names the label set source

- **WHEN** a run finishes
- **THEN** the summary records the label set run id and hash
