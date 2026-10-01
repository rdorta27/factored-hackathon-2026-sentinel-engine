# Spec Delta

## ADDED Requirements

### Requirement: Persistent state with retention

Sessions, conversation state and cases SHALL be stored in a configurable backend (`SENTINEL_STATE_BACKEND`: `sqlite` by default at `SENTINEL_DB_PATH`, or `memory`), so a restart keeps live sessions, pending confirmations and cases. Stored session and conversation keys SHALL be hashes of the session token, never the token. The conversation state, which includes customer turns, SHALL be deleted on logout and when an expired session is presented, and conversations without a live session SHALL be purged on login. Login-attempt counters MAY stay per process. Traces to REQ-0027 (P0, In progress) and REQ-0001 (P0, In progress).

#### Scenario: A restart keeps the conversation

- **WHEN** the process restarts between the confirm box and the confirmation
- **THEN** the same cookie confirms the pending charge and the case is created once

#### Scenario: Logout deletes the conversation

- **WHEN** a customer logs out
- **THEN** no conversation state for that session remains

#### Scenario: Expiry deletes the conversation

- **WHEN** an expired session is presented
- **THEN** the system returns 401 and deletes that session's conversation state
