# resolution-evaluation Specification

## Purpose

Measures safe automated resolution on a labelled multi-turn set over the mock store, with the baseline and the router on the same cases, judged by rules committed before the run.

## Requirements

### Requirement: A multi-turn resolution set over the mock store

The system SHALL keep a set of cases that each name the account country, the language variant, the opening message, the charge to select, whether to confirm, the expected outcome and whether a handoff is the right outcome. The set SHALL cover charges that must resolve (eligible and approved), and charges that must not: outside the window, pending, refunded, already disputed, above the high-amount limit, above the fraud-score limit, and a customer who states the charge is not theirs. Each case SHALL belong to a situation, defined by the charge and the rule it exercises, and the variants of one situation SHALL share it. The set SHALL use only the charges present in the mock store and SHALL say how many distinct situations it covers. Traces to REQ-0055 (P0, In progress) and REQ-0022 (P0, Done).

#### Scenario: Every case is labelled

- **WHEN** the set is loaded
- **THEN** every case carries country, variant, charge, expected outcome and the handoff label, and a case missing one is rejected

#### Scenario: Both kinds of outcome are present

- **WHEN** the set is counted
- **THEN** it holds cases that should resolve and cases that should be refused or handed off, and states how many of each

#### Scenario: Situations are counted

- **WHEN** the set is described in a report
- **THEN** it states the number of cases and the number of distinct situations

### Requirement: Baseline and router on the same cases, measured once

One run SHALL execute the keyword baseline and `router_v2` on the same cases and report each version's results next to the other. The router's answers SHALL be recorded once under a spend cap and replayed offline afterwards. Both versions SHALL use the same session, store and reference date. The run SHALL be frozen write-once under `evidence/evaluation-runs/` and SHALL NOT edit any earlier run, including `2024Q4-eval-v7` and the sealed set's `measured.json` entry. Traces to REQ-0016 (P0, Done), REQ-0020 (P0, Done) and REQ-0055 (P0, In progress).

#### Scenario: Both versions see identical cases

- **WHEN** the run is frozen
- **THEN** the case ids are identical for the baseline and the router

#### Scenario: Replay needs no network

- **WHEN** the run is replayed from the recordings
- **THEN** it opens no connection and reproduces the frozen outcomes

#### Scenario: Earlier runs are untouched

- **WHEN** the new run is frozen
- **THEN** no file of an earlier run and no entry of `measured.json` changes

### Requirement: Acceptance rules are committed before the run

The rules that judge the result SHALL be written in the repository and committed before the run exists. They SHALL state, in cases: the unsafe-outcome limit, the limit on missed transfers, how a difference between baseline and router is judged, and what is reported when a rule fails. The result SHALL be judged by those rules without change, and a failed rule SHALL be reported as it is. Traces to REQ-0017 (P0, In progress) and REQ-0055 (P0, In progress); decision 018.

#### Scenario: Rules precede the run

- **WHEN** the commit order is read
- **THEN** the rules are committed before the frozen run

#### Scenario: A failed rule is reported

- **WHEN** a version fails a rule
- **THEN** the report states the failure with its cases and no rule is edited to fit the result

### Requirement: Resolution is reported with its denominators and limits

The report SHALL give safe automated resolution over all in-scope cases, the share of in-scope cases where automation was attempted, containment, missed and unnecessary transfers, unsafe outcomes with counts and denominators, p50 and p95 latency, and cost per attempted case and per successful resolution (not defined when there are none). A resolution SHALL be unsafe if it opens a case that policy refuses or that the case marks must-not-pass. Confidence intervals SHALL be computed by resampling situations, not cases. The report SHALL label the measurement a simulation over a mock store, state the number of cases and situations, and SHALL NOT present the rate as a field resolution rate. Traces to REQ-0055 (P0, In progress), REQ-0022 (P0, Done), REQ-0013 (P0, In progress) and REQ-0057 (P1, In progress).

#### Scenario: Resolution is greater than zero where it should be

- **WHEN** eligible approved charges are confirmed by the system
- **THEN** safe automated resolution is reported over the in-scope cases with its numerator and denominator

#### Scenario: A refused charge opened is unsafe

- **WHEN** a version opens a case on a charge that policy refuses
- **THEN** the case is counted as an unsafe outcome and listed

#### Scenario: The label is explicit

- **WHEN** the report is read
- **THEN** it states that the result is a simulation over a mock store with the case and situation counts
