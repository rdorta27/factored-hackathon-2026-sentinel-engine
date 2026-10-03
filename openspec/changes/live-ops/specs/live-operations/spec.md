## ADDED Requirements

### Requirement: The deploy keeps a stable session salt

The deploy SHALL read the session salt from the environment or `.env` and SHALL stop with an error when it is missing; it SHALL NOT generate a new salt. The salt SHALL reach the app as a secret reference. Traces to REQ-0027 (P0, Done) and REQ-0034 (P0, Done).

#### Scenario: Missing salt stops the deploy

- **WHEN** the deploy runs without `SENTINEL_SESSION_SALT`
- **THEN** it exits with an error before changing the container app

#### Scenario: Records correlate across redeploys

- **WHEN** the same session identifier is hashed before and after a redeploy
- **THEN** both records carry the same `session_ref`

### Requirement: The public service proves durability after a redeploy

After each redeploy, a check SHALL confirm the served model and prompt version, that the locale files carry the keys of the merged code, and that a handoff ticket and a dispute created before a revision restart are readable after it. The result SHALL be recorded without identifiers. Traces to REQ-0035 (P0, Done), REQ-0027 (P0, Done) and REQ-0052 (P0, In progress).

#### Scenario: A handoff survives a restart

- **WHEN** a ticket is filed and the revision restarts
- **THEN** the advisor view still lists it

#### Scenario: The served code is the merged code

- **WHEN** the locale file is fetched after the redeploy
- **THEN** it contains `charge.not_found` and `extraction.refused`

### Requirement: Turn records are queried by country, outcome and language

Saved queries over the platform log SHALL report, per account country, outcome and language, the number of turns, p50 and p95 latency, failed or timed-out steps, handoffs and cost, using only turn-record fields. Results SHALL be recorded as aggregates with the period and the number of turns read. Traces to REQ-0050 (P1, In progress), REQ-0025 (P1, Done) and REQ-0052 (P0, In progress).

#### Scenario: Queries return per-country aggregates

- **WHEN** the queries run after demo traffic
- **THEN** they return one row per country and outcome with counts and latency percentiles, and no trace id or text

### Requirement: The workflow replays frozen runs

The test workflow SHALL run `python3 -m eval.run verify` for every frozen run listed as replayable, and a run SHALL be listed only after it verifies offline. Traces to REQ-0028 (P0, Done) and REQ-0022 (P0, Done).

#### Scenario: A drifted run fails the check

- **WHEN** a change makes a listed run differ from its frozen summary
- **THEN** the workflow fails
