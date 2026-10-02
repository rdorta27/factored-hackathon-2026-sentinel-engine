## ADDED Requirements

### Requirement: The Gold file is chosen explicitly

The DuckDB Gold file SHALL be taken from `SENTINEL_GOLD_DUCKDB` when set, otherwise from one path fixed relative to the repository, and SHALL NOT depend on the folder the process was started from. When `SENTINEL_GOLD_SOURCE` is `mock`, no file SHALL be read. The chosen source SHALL be reported by `GET /api/v1/health`. Traces to REQ-0015 (P0, Done), REQ-0028 (P0, Done) and REQ-0032 (P1, Done).

#### Scenario: Same result from any folder

- **WHEN** the app starts from the repository root and from `sentinel-ai-core/` with the same settings
- **THEN** both report the same Gold source

#### Scenario: Mock is honoured

- **WHEN** `SENTINEL_GOLD_SOURCE` is `mock` and the file exists
- **THEN** the app reports `mock` and reads no file

### Requirement: Real rows are limited to the reference date

The DuckDB adapter SHALL NOT return a row dated after the configured reference date, and SHALL filter by the session customer in the query. Traces to REQ-0039 (P0, Done) and REQ-0007 (P0, Done).

#### Scenario: A future-dated row is not listed

- **WHEN** a customer has a row dated after the reference date
- **THEN** it does not appear and cannot be selected

### Requirement: Local users for real customers stay out of the repository

The repository SHALL provide a script that writes a users file for real Gold customers (login, customer id, country, role, salted password hash) to a path ignored by git, choosing customers with a recent approved charge per country and customers that trigger each handoff rule. The script SHALL print counts only and SHALL NOT write identifiers, rows or the data location to any tracked file. Traces to REQ-0034 (P0, Done), REQ-0009 (P0, In progress) and REQ-0031 (P0, Done).

#### Scenario: Counts only

- **WHEN** the script finishes
- **THEN** it prints how many users it wrote per country and no identifier

#### Scenario: Output is ignored by git

- **WHEN** the output path is checked
- **THEN** git ignores it

### Requirement: Real-data evidence has no rows

Evidence of a run on real Gold SHALL contain only the source label and outcomes per scenario and language, never a row, a customer id, a transaction id or the data location. Traces to REQ-0034 (P0, Done) and REQ-0009 (P0, In progress).

#### Scenario: Evidence holds no identifiers

- **WHEN** the recorded evidence is searched
- **THEN** it contains no customer id, transaction id or data path
