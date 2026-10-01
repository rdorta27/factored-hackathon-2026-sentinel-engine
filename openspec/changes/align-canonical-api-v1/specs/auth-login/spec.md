# Spec Delta

## REMOVED Requirements

### Requirement: Mock credential login

**Reason**: Duplicated by `session` "Test-session login", which is what the app implements.
**Migration**: Use `POST /api/v1/session/login` with `login` and `password`.

### Requirement: Opaque server-side session with expiry and revocation

**Reason**: Duplicated by `session` "Opaque server-side session with expiry and revocation".
**Migration**: Use the `session` requirement; `GET /auth/me` is `GET /api/v1/session/me`.

### Requirement: Session-derived identity only

**Reason**: Duplicated by `session` "Session-derived identity only".
**Migration**: Use the `session` requirement.

### Requirement: Login attempt limiting

**Reason**: Duplicated by `session` "Login attempt limiting".
**Migration**: Use the `session` requirement.

### Requirement: Authentication audit log

**Reason**: Duplicated by `session` "Authentication audit log".
**Migration**: Use the `session` requirement.
