# Proposal: sentinel-login (mock test login + session)

## Why

The Tuesday skeleton needs an authenticated session before any chat or tool call exists. Without it, `POST /chat` cannot isolate customers per session (REQ-0007), and the demo login would be a decoration. This change delivers the login mock now so the backend seam is real from day one.

## What Changes

- Add `sentinel-login/` package (Python 3.12, FastAPI, Pydantic v2): `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- Opaque server-side sessions: `secrets.token_urlsafe(32)`, TTL with expiry enforcement, revocation on logout.
- Mock credential check: `customer_id` plus test password verified with PBKDF2-HMAC-SHA256 (stdlib `hashlib`) and `hmac.compare_digest`; identical generic 401 for unknown user or wrong password.
- `customer_id` is exposed only from the validated session object; no endpoint accepts it from the client body.
- JSON-lines audit log for `login_success`, `login_failed`, `login_locked`, `logout`, `session_expired`, `access_denied` with timestamp, `customer_id`, and `trace_id`; no passwords or full tokens logged.
- Login rate limiting: 5 failures per `customer_id` and per IP, then 15-minute lockout.
- Strict Pydantic v2 schemas (`extra="forbid"`, length limits, `customer_id` pattern).

## Capabilities

### New Capabilities

- `auth-login`: mock test login, server-side session lifecycle (create, validate, expire, revoke), and audit events for authentication.

### Modified Capabilities

- None (no existing specs exist yet; `openspec list --specs` returns empty).

## Impact

- New code: `sentinel-login/` only. No changes to `docs/`, `evidence/`, or existing decisions.
- Dependencies: Python 3.12, `fastapi`, `uvicorn`, `pydantic` (v2) for runtime; `pytest`, `httpx` for tests. No JWT, hashing, or settings libraries (stdlib covers KDF and secrets).
- Contracts: `POST /auth/login` (JSON `customer_id` + `password`, sets HttpOnly session cookie), `POST /auth/logout` (idempotent), `GET /auth/me` (returns session `customer_id`). Mocks implement `UserRepository` / `SessionStore` protocols so a real store can replace them without contract changes.
- Traces to REQ-0007 (policies and session in code) and the session rules in `docs/build/security.md`; implements backend decision `docs/build/decisions/005-backend.md`.

## Non-goals

- `POST /chat`, the orchestrator, LLM routes, tools, disputes store, and the one-page chat UI (`docs/build/decisions/006-frontend.md`) are out of scope.
- No real identity provider, no production user data, no dataset rows in the repo.
- No multi-worker shared sessions (single-process store documented as a limit; decision on shared store belongs to the deploy change).
