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

### Requirement: The final redeploy is proved and queried

After the final redeploy, a check SHALL confirm the served model and prompt version, the locale keys of the merged code, the demo personas and the three demo cases, and saved queries SHALL report turns, p50 and p95 latency, failed or timed-out steps, handoffs and cost per account country, outcome and language. Results SHALL be recorded as aggregates without identifiers. Traces to REQ-0035 (P0, Done), REQ-0050 (P1, In progress) and REQ-0052 (P0, In progress).

#### Scenario: The served code is the merged code

- **WHEN** the locale file is fetched after the redeploy
- **THEN** it contains the keys added by the merged changes

#### Scenario: Queries return per-country aggregates

- **WHEN** the queries run after demo traffic
- **THEN** they return one row per country, outcome and language with counts and latency percentiles, and no trace id or text
