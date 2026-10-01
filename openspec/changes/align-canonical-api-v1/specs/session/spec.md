# Spec Delta

## MODIFIED Requirements

### Requirement: Role is stored and only the customer path is exercised

The system SHALL store one role on the session. This change SHALL exercise only the `customer` role. A customer session SHALL be able to call chat and the transaction listing. Session routes SHALL be `POST /api/v1/session/login`, `POST /api/v1/session/logout`, and `GET /api/v1/session/me`; `me` SHALL return the role and country and SHALL NOT return `customer_id`. Traces to REQ-0027 (P0, In progress) and REQ-0047 (P0, In progress).

#### Scenario: Customer session reaches chat

- **WHEN** a customer session posts to `/api/v1/chat`
- **THEN** the request is not rejected for role

#### Scenario: Me does not expose the identifier

- **WHEN** a customer session calls `GET /api/v1/session/me`
- **THEN** the response contains the role and country only
