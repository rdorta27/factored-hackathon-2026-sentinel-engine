## ADDED Requirements

### Requirement: The deploy keeps a stable session salt

The deploy SHALL read the session salt from the environment or `.env` and SHALL stop with an error when it is missing; it SHALL NOT generate a new salt. The salt SHALL reach the app as a secret reference. Traces to REQ-0027 (P0, Done) and REQ-0034 (P0, Done).

#### Scenario: Missing salt stops the deploy

- **WHEN** the deploy runs without `SENTINEL_SESSION_SALT`
- **THEN** it exits with an error before changing the container app

### Requirement: The workflow replays frozen runs

The test workflow SHALL run `python3 -m eval.run verify` for every frozen run listed as replayable, and a run SHALL be listed only after it verifies offline. Traces to REQ-0028 (P0, Done) and REQ-0022 (P0, Done).

#### Scenario: A drifted run fails the check

- **WHEN** a change makes a listed run differ from its frozen summary
- **THEN** the workflow fails
