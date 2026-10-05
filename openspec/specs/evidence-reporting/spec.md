# evidence-reporting Specification

## Purpose
Defines how each evaluation summary reports its independent sample size, its latency and cost, and its negative results, so a reader can judge the evidence.

## Requirements

### Requirement: Every evaluation summary states its independent sample size

Each evaluation summary SHALL report the number of cases and the number of bases next to each other. Confidence intervals SHALL resample by base. Traces to REQ-0022 (P0, Done).

#### Scenario: Cases from few bases

- **WHEN** a summary covers 405 cases from 70 bases
- **THEN** the summary and the report show both numbers and the interval resamples by base

### Requirement: The resolution gap is explained by data

The evaluation SHALL state, for the resolution set, the ceiling of safe resolution and the cases where the baseline and the router differ. Traces to REQ-0055 (P0, Done) and REQ-0022 (P0, Done).

#### Scenario: No difference in resolution

- **WHEN** the paired difference in safe resolution is 0
- **THEN** the report lists each case as resolved by both, failed by both, or different
- **AND** the report states the cause: a ceiling set by policy and data, or a set that cannot separate the systems

### Requirement: Latency and cost come from a live run

The report SHALL give p50 and p95 latency per call and per conversation, and cost per attempted case and per successful resolution, from a live model run with a spend cap. A replay time SHALL NOT appear as end-to-end latency. Traces to REQ-0055 (P0, Done).

#### Scenario: Replay time

- **WHEN** a number comes from a replay
- **THEN** the report labels it as a replay and does not call it latency

#### Scenario: Spend cap

- **WHEN** the spend reaches the cap
- **THEN** the run stops and the summary says that the cap stopped it

### Requirement: Negative results and known limits are published

The documentation SHALL record each rejected component, each attack case that passes only on the stand-in model, and each documented limitation, with the rule that decided it. Traces to REQ-0021 (P0, Done) and REQ-0013 (P0, In progress).

#### Scenario: Attack case on the stand-in model

- **WHEN** an attack case passes only because the model is a stand-in
- **THEN** the case runs against the real model and the outcome goes in a new adversarial run
