# auth-login Specification

## Purpose

Provides the mock test login and server-side session that all later backend endpoints use to isolate customers, so authentication is real from the first skeleton.

## Requirements

### Requirement: Mock credential login

The system SHALL authenticate a test customer with `customer_id` plus a test password, and SHALL return the same generic failure for an unknown user and for a wrong password. Traces to REQ-0007 (P0, Pending): policies and session enforced in code.

#### Scenario: Successful login

- **WHEN** a client posts known `customer_id` with the correct test password
- **THEN** the system creates a session and returns 200 with the session cookie set

#### Scenario: Wrong password is generic

- **WHEN** a client posts a known `customer_id` with a wrong password
- **THEN** the system returns 401 with the generic message and records `login_failed`

#### Scenario: Unknown user is indistinguishable

- **WHEN** a client posts an unknown `customer_id`
- **THEN** the system returns the identical 401 generic message and records `login_failed`

### Requirement: Opaque server-side session with expiry and revocation

The system SHALL issue an opaque random session token, SHALL reject expired sessions, and SHALL revoke the session on logout. Logout SHALL be idempotent. Traces to REQ-0007 (P0, Pending).

#### Scenario: Session identifies the customer

- **WHEN** a client calls `GET /auth/me` with a valid session cookie
- **THEN** the system returns the session `customer_id` with 200

#### Scenario: Expired session is rejected and cleared

- **WHEN** a client presents a session past its expiry
- **THEN** the system deletes the session, returns 401, and records `session_expired`

#### Scenario: Logged-out token stays dead

- **WHEN** a client presents a token after logout
- **THEN** the system returns 401 and records `access_denied`

### Requirement: Session-derived identity only

The system SHALL derive `customer_id` exclusively from the validated session and SHALL reject any client-supplied `customer_id` in auth-adjacent bodies. Traces to REQ-0007 (P0, Pending).

#### Scenario: Foreign identifier in body is rejected

- **WHEN** a request body contains a `customer_id` field alongside credentials
- **THEN** the system rejects the request with 422 before running authentication logic

### Requirement: Login attempt limiting

The system SHALL lock out further login attempts for a `customer_id` and source IP after 5 consecutive failures for 15 minutes, and SHALL reset the counter on success. Traces to REQ-0007 (P0, Pending).

#### Scenario: Lockout after repeated failures

- **WHEN** a client fails login 5 times for the same `customer_id`
- **THEN** the next attempt is rejected as locked and records `login_locked`

### Requirement: Authentication audit log

The system SHALL append a JSON-lines audit record with timestamp, `customer_id`, and `trace_id` for login success, login failure, lockout, logout, session expiry, and denied access, and SHALL never log passwords or full session tokens. Traces to REQ-0007 (P0, Pending).

#### Scenario: Audit record is complete and safe

- **WHEN** any authentication event occurs
- **THEN** the log line contains timestamp, event name, `customer_id`, and `trace_id`, and contains no password or full token
