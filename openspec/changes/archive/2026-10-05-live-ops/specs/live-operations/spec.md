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

### Requirement: One script checks the end-to-end behavior

`scripts/e2e_check.py` SHALL run the three demo cases and the manual test replay against a base URL, print one table of pass or fail, and exit with a non-zero code on a failure. On a remote URL it SHALL enter by password with credentials read from the file named by `SENTINEL_E2E_CREDENTIALS_FILE`, and SHALL NOT print or log a password. Traces to REQ-0028 (P0, Done) and REQ-0035 (P0, Done).

#### Scenario: Remote URL without credentials

- **WHEN** the base URL is remote, the one-click route answers 404 and the variable is not set
- **THEN** the script stops with a clear message before any chat request

#### Scenario: Loopback URL

- **WHEN** the base URL is loopback
- **THEN** the script starts a local app with a clean SQLite file and the Gold mock

### Requirement: The access check proves that the link has no passwordless entry

`scripts/e2e_check.py --access-check` SHALL check that the persona route answers 404, that the documented fixture password fails with HTTP 401 for each of the four logins with one failed attempt for each, and that each judge credential logs in with the expected role and country. Traces to REQ-0027 (P0, Done).

#### Scenario: Fixture password on the link

- **WHEN** the check logs in with a documented fixture password
- **THEN** the login fails and the lockout does not trigger

### Requirement: The state of the link can be reset

`deploy/azure/reset-state.sh` SHALL remove the SQLite file and the turn log from the Azure Files share and SHALL check that `GET /api/v1/health` answers afterwards. Traces to REQ-0035 (P0, Done).

#### Scenario: Reset after tests

- **WHEN** the owner runs the script after the tests on the link
- **THEN** the link holds no session, dispute or ticket from the tests
