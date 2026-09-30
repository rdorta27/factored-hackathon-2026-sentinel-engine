# Spec Delta

## MODIFIED Requirements

### Requirement: Authentication audit log

The system SHALL append a JSON-lines record in the observability format with `step: session` for login success, login failure, lockout, logout, session expiry, and denied access. The record SHALL carry a salted `session_ref` hash instead of the customer, SHALL NOT contain the client IP, and SHALL never log passwords, confirmation tokens, or full session tokens. Traces to REQ-0007 (P0, In progress) and REQ-0047 (P0, In progress).

#### Scenario: Audit record is complete and safe

- **WHEN** any authentication event occurs
- **THEN** the log line contains timestamp, event name, salted `session_ref`, and `trace_id`, and contains no password, no client IP, no customer identifier, and no full token
