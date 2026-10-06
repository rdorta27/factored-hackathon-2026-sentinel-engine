## ADDED Requirements

### Requirement: Each sealed set is measured once

The measurement command SHALL verify the seal of `sealed_v8` and of `sealed_v8b`, SHALL refuse a hash that `eval/measured.json` already lists, and SHALL record a hash only after the run is frozen. Traces to REQ-0017 (P0, Done) and REQ-0020 (P0, Done).

#### Scenario: A second measurement

- **WHEN** the command runs on a sealed set that is already measured
- **THEN** it refuses and calls no model

#### Scenario: A failed run

- **WHEN** the run stops before it is frozen
- **THEN** `eval/measured.json` is unchanged

### Requirement: The verdict applies the rules of decision 018

A script SHALL print, for each candidate, the result of each gate and the served choice. v3 SHALL be the default only if it passes every gate. Otherwise v2 SHALL stay the default and the report SHALL name the failed rule. Traces to REQ-0016 (P0, Done) and REQ-0055 (P0, Done).

#### Scenario: A gate fails

- **WHEN** v3 fails a gate
- **THEN** the verdict names the gate and the served choice is v2

### Requirement: The measurement states its sample size and its limits

Every number SHALL state its sample size, its bases, its type (simulation) and the model and prompt versions. Traces to REQ-0022 (P0, Done).

#### Scenario: A frozen run

- **WHEN** the run is frozen
- **THEN** every metric in the summary carries `n`
