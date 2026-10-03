## ADDED Requirements

### Requirement: Checks run on every change without secrets

Both test suites SHALL run on every push and pull request, one result per package, without model keys, cloud credentials or data, without live model calls and without writing evidence. Frozen runs listed as replayable SHALL be verified offline in the same workflow. Traces to REQ-0028 (P0, Done), REQ-0021 (P0, Done) and REQ-0034 (P0, Done).

#### Scenario: A broken test fails the check

- **WHEN** a pull request makes a test fail in either package
- **THEN** the check fails

#### Scenario: No evidence is written

- **WHEN** the adversarial tests run in the workflow
- **THEN** no folder appears under `evidence/`

### Requirement: Attack status changes fail loudly

A `blocked_verified` attack that stops being blocked, or a `no_defense_yet` attack that starts passing, SHALL fail the check. Traces to REQ-0021 (P0, Done).

#### Scenario: A defence regresses

- **WHEN** a change lets a blocked attack through
- **THEN** the check fails
