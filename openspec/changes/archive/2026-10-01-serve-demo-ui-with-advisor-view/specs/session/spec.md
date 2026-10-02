# Spec Delta

## REMOVED Requirements

### Requirement: Role is stored and only the customer path is exercised

**Reason**: A second role (advisor) is now exercised and the session paths moved to `/api/v1/auth/*`.
**Migration**: Use "Roles and demo login" below and the `roles` capability.

## ADDED Requirements

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
