# Tasks: sentinel-login

## 1. Scaffold package

- [x] 1.1 Create `sentinel-login/` package layout with Python 3.12 (`pyproject.toml` `requires-python`, FastAPI/uvicorn/pydantic runtime, pytest/httpx test deps), owner Felix, per `docs/build/decisions/005-backend.md`; verify with `python --version` and `pip install -e ./sentinel-login` succeeding — evidence: `sentinel-login/pyproject.toml`.
- [x] 1.2 Add mock user fixture (`app/auth/mocks/users.json`, invented `CUST-0001` only, no dataset rows) with PBKDF2 salt/hash fields, owner Felix, per `docs/build/areas/ai.md` mock-contract practice; verify the file loads as JSON and contains no real data — evidence: `sentinel-login/app/auth/mocks/users.json`.

## 2. Session and credential core

- [x] 2.1 Implement `UserRepository`/`SessionStore` protocols plus JSON mock and in-memory store with TTL/expiry/revocation, owner Felix, per `docs/build/decisions/005-backend.md`; verify with unit tests for create/validate/expire/revoke — evidence: `sentinel-login/tests/test_session_store.py`.
- [x] 2.2 Implement credential verification (PBKDF2-HMAC-SHA256 stdlib, per-user salt, `hmac.compare_digest`, identical generic failure for unknown user vs wrong password), owner Felix, per `docs/build/security.md` authentication rules; verify with unit tests for success/wrong-password/unknown-user — evidence: `sentinel-login/tests/test_credentials.py`.

## 3. HTTP layer and audit

- [x] 3.1 Implement `POST /auth/login`, `POST /auth/logout` (idempotent), `GET /auth/me`, session cookie (`HttpOnly`, `SameSite=Lax`, `Secure` by env), `require_session` dependency, and strict Pydantic v2 schemas (`extra="forbid"`, limits, `customer_id` pattern), owner Felix, per `docs/build/decisions/005-backend.md`; verify with endpoint tests including smuggled-`customer_id` 422 — evidence: `sentinel-login/tests/test_auth_endpoints.py`.
- [x] 3.2 Implement login rate limiting (5 failures per `customer_id` and per IP, 15-minute lockout, reset on success) and JSON-lines audit log with `trace_id` middleware (never passwords/full tokens), owner Felix, per `docs/build/security.md` audit rules; verify with lockout and audit-content tests — evidence: `sentinel-login/tests/test_auth_limits_audit.py`.

## 4. Attack verification and docs

- [x] 4.1 Run the attack matrix from the spec (invalid token, expired session, reused post-logout token, foreign `customer_id`, lockout) against `/docs` and record results, owner Felix, per `docs/build/security.md` adversarial practice; verify all scenarios return the specified 401/422 with audit events — evidence: `openspec/changes/sentinel-login/attack-checks.md`.
