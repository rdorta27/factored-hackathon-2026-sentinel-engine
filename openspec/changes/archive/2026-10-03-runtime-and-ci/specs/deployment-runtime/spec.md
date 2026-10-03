# Spec Delta

## Purpose

Defines what the deployed container owes at runtime: turn records visible in the platform log and state that outlives the container, so a restart never loses a session, dispute or handoff.

## ADDED Requirements

### Requirement: Turn records reach the platform log

When standard-output logging is enabled, the service SHALL print every turn record as one JSON line identical to the file line, carrying no personal data; when disabled, behaviour SHALL be unchanged. Traces to REQ-0025 (P1, Done), REQ-0047 (P0, Done) and REQ-0052 (P0, In progress).

#### Scenario: A turn appears on standard output

- **WHEN** the setting is on and a chat turn completes
- **THEN** each record is printed as one JSON line equal to the file line

#### Scenario: Off by default

- **WHEN** the setting is absent
- **THEN** nothing is printed

### Requirement: State survives a restart in the deployment

The deployed service SHALL keep its SQLite file and turn log on storage that outlives the container, with a configurable SQLite journal mode supported by that storage and one replica. After a restart, an unexpired session, an open dispute and a handoff ticket SHALL still be readable, and logout SHALL still delete the conversation. Traces to REQ-0027 (P0, Done), REQ-0035 (P0, Done) and REQ-0052 (P0, In progress).

#### Scenario: A handoff survives a restart

- **WHEN** a ticket is filed and the container restarts
- **THEN** the advisor view still lists it

#### Scenario: Journal mode follows the setting

- **WHEN** the journal mode is set to `DELETE`
- **THEN** the database opens in that mode
