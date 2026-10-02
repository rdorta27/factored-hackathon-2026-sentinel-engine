# session Specification

## Purpose

Gives the submission app a server-side test session so every later call derives the customer from the cookie, and so the demo date is one value shared by the window, the listing, and the receipt.

## Requirements

### Requirement: Test-session login

The system SHALL authenticate a test customer with a documented false credential and SHALL return the same generic failure for an unknown user and for a wrong password. It SHALL NOT accept a client-supplied `customer_id` as the identity to use after login. Traces to REQ-0027 (P0, Pending) and REQ-0007 (P0, Pending).

#### Scenario: Successful login

- **WHEN** a client posts a known test customer with the correct test password
- **THEN** the system creates a session and returns 200 with the session cookie set

#### Scenario: Wrong password is generic

- **WHEN** a client posts a known test customer with a wrong password
- **THEN** the system returns 401 with the generic message and records `login_failed`

#### Scenario: Unknown user is indistinguishable

- **WHEN** a client posts an unknown customer
- **THEN** the system returns the identical 401 generic message and records `login_failed`

### Requirement: Opaque server-side session with expiry and revocation

The system SHALL issue an opaque random session token, SHALL reject expired sessions, and SHALL revoke the session on logout. Logout SHALL be idempotent. An expired or revoked session SHALL NOT call a tool. Traces to REQ-0027 (P0, Pending) and REQ-0007 (P0, Pending).

#### Scenario: Current session identifies the customer

- **WHEN** a client requests the current session with a valid cookie
- **THEN** the system returns the session customer and country with 200

#### Scenario: Expired session is rejected and cleared

- **WHEN** a client presents a session past its expiry
- **THEN** the system deletes the session, returns 401, and records `session_expired`

#### Scenario: Logged-out token stays dead

- **WHEN** a client presents a token after logout
- **THEN** the system returns 401 and records `access_denied`

### Requirement: Session-derived identity only

The system SHALL derive `customer_id` exclusively from the validated session and SHALL reject any client-supplied `customer_id` in the login body. The login, logout, and current-session operations SHALL NOT be served on `/auth/*`. Traces to REQ-0047 (P0, Pending) and REQ-0027 (P0, Pending).

#### Scenario: Foreign identifier in the login body is rejected

- **WHEN** a login body contains a `customer_id` field alongside credentials
- **THEN** the system rejects the request with 422 before running authentication logic

### Requirement: Login attempt limiting

The system SHALL lock out further login attempts for a customer and source IP after 5 consecutive failures for 15 minutes, and SHALL reset the counter on success. Traces to REQ-0007 (P0, Pending).

#### Scenario: Lockout after repeated failures

- **WHEN** a client fails login 5 times for the same customer
- **THEN** the next attempt is rejected as locked and records `login_locked`

### Requirement: Authentication audit log

The system SHALL append a JSON-lines record in the observability format with `step: session` for login success, login failure, lockout, logout, session expiry, and denied access. The record SHALL carry a salted `session_ref` hash instead of the customer, SHALL NOT contain the client IP, and SHALL never log passwords, confirmation tokens, or full session tokens. Traces to REQ-0007 (P0, In progress) and REQ-0047 (P0, In progress).

#### Scenario: Audit record is complete and safe

- **WHEN** any authentication event occurs
- **THEN** the log line contains timestamp, event name, salted `session_ref`, and `trace_id`, and contains no password, no client IP, no customer identifier, and no full token

### Requirement: Reference date is read once

The system SHALL read its notion of today from `SENTINEL_REFERENCE_DATE`, defaulting to `2026-06-17` when the variable is unset, and SHALL use that value for the filing window, the transaction as-of mark, and the date shown to the customer. It SHALL NOT read the wall clock for that window. Traces to REQ-0039 (P0, Pending).

#### Scenario: Default reference date is the dataset end

- **WHEN** the variable is unset
- **THEN** the system uses `2026-06-17`

#### Scenario: Environment override wins

- **WHEN** the variable is set to another date
- **THEN** the window check and the displayed date both use it

### Requirement: Persistent state with retention

Sessions, conversation state and cases SHALL be stored in a configurable backend (`SENTINEL_STATE_BACKEND`: `sqlite` by default at `SENTINEL_DB_PATH`, or `memory`), so a restart keeps live sessions, pending confirmations and cases. Stored session and conversation keys SHALL be hashes of the session token, never the token. The conversation state, which includes customer turns and `rejected_ids`, SHALL be deleted on logout and when an expired session is presented, and conversations without a live session SHALL be purged on login. Per-session `history` SHALL be bounded to 50 entries and `actions` to 200 entries with an `overflow` mark on discard. Login-attempt counters MAY stay per process. Traces to REQ-0027 (P0, In progress) and REQ-0001 (P0, In progress).

#### Scenario: A restart keeps the conversation

- **WHEN** the process restarts between the confirm box and the confirmation
- **THEN** the same cookie confirms the pending charge and the case is created once

#### Scenario: Logout deletes the conversation

- **WHEN** a customer logs out
- **THEN** no conversation state for that session remains

#### Scenario: Expiry deletes the conversation

- **WHEN** an expired session is presented
- **THEN** the system returns 401 and deletes that session's conversation state

#### Scenario: Bounded retention keeps the session usable

- **WHEN** a session exceeds the history or actions bound
- **THEN** the oldest entries are discarded with the `overflow` mark and the session keeps working

### Requirement: Roles and demo login

The system SHALL expose `POST /api/v1/auth/login`, `POST /api/v1/auth/logout` and `GET /api/v1/auth/me`, and SHALL always require a password; there SHALL be no login by customer number alone. The session SHALL store one role. Customer fixture users SHALL always load; non-customer demo users (the advisor) SHALL load only when `SENTINEL_DEMO_AUTH=1`, and otherwise SHALL fail like any unknown user. `me` SHALL return the role and country and SHALL NOT return `customer_id`. Traces to REQ-0027 (P0, In progress), REQ-0007 (P0, In progress), and REQ-0028 (P0, In progress).

#### Scenario: Advisor does not exist without the flag

- **WHEN** the advisor credential is used and `SENTINEL_DEMO_AUTH` is not `1`
- **THEN** the system returns the generic 401

#### Scenario: Password is always required

- **WHEN** a login omits the password or sends `customer_id` instead of `login`
- **THEN** the system returns 422

#### Scenario: Old session paths are gone

- **WHEN** a client posts to `/api/v1/session/login`
- **THEN** the system returns 404
