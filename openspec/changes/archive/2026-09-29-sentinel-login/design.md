# Design: sentinel-login

## Context

See proposal.md (Why). Constraints: Python 3.12, FastAPI + Pydantic v2, no extra runtime libraries; code, comments, and names in English; mocks replaceable without contract changes; `docs/build/security.md` session rules and REQ-0007. OpenSpec project has no specs yet, so `auth-login` is a new flat capability.

## Goals / Non-Goals

**Goals:**

- Small `sentinel-login/` package with `auth`, `session`, `audit` modules and a `main.py` that mounts the three auth endpoints.
- Session seam (`require_session` dependency) that later endpoints reuse so `customer_id` never comes from the client.

**Non-Goals:**

- `POST /chat`, orchestrator, tools, UI, and deploy topology stay out; single-process in-memory stores are accepted with the multi-worker limit documented.

## Decisions

- **Opaque token over JWT.** `secrets.token_urlsafe(32)` with a server-side `token -> Session` store gives logout revocation and expiry deletion for free. JWT would need a denylist (state anyway) plus a new library, for zero gain here. Alternative rejected: JWT stateless.
- **PBKDF2 from stdlib over passlib.** `hashlib.pbkdf2_hmac("sha256", 600_000)` with per-user 16-byte salt meets the credential-storage bar with no dependency. Mock passwords are documented demo values, never real secrets. Alternative rejected: `passlib`/`bcrypt` packages.
- **Cookie transport over body echo.** `HttpOnly`, `SameSite=Lax`, `Path=/`, `Secure` by environment. The frontend (decision 006) then sends no session in the body, which shrinks the attack surface; the one stale sentence in 006 ("message and the session") is flagged for a doc fix, not implemented here.
- **Two-belt identity.** Endpoints take no `customer_id` parameter (belt 1); schemas set `extra="forbid"` so a smuggled `customer_id` fails with 422 (belt 2).
- **Constant-shape failures.** Unknown user runs the same KDF work as a wrong password and returns the identical 401, so neither message nor timing reveals which customers exist.
- **Protocols for mocks.** `UserRepository` and `SessionStore` are `Protocol`s; the JSON-file mock is one adapter. A SQL adapter later swaps in without touching services or contracts (decision 005).
- **JSON-lines audit + trace middleware.** One logger, fields `ts`, `event`, `customer_id`, `trace_id`, `ip`; token fingerprint `sha256(token)[:12]` when session identity is needed in logs. `X-Trace-Id` returned per request.

## Risks / Trade-offs

- [Risk] In-memory sessions die on restart and break under multiple workers/replicas → Mitigation: document `workers=1` for the demo; `SessionStore` protocol already allows a SQLite/Redis swap in the deploy change.
- [Risk] Cookie transport implies CSRF residual → Mitigation: `SameSite=Lax` plus same-origin JSON-only API; custom-header hardening deferred to the chat change.
- [Risk] No request body size limit in Starlette by default → Mitigation: strict `max_length` on fields now; payload-size middleware deferred and recorded as an open task.
- [Risk] Proxy IP spoofing for rate limiting → Mitigation: define the trusted IP source before the Azure deploy; never trust `X-Forwarded-For` by default.

## Migration Plan

1. Merge this change; `sentinel-login` runs standalone on `uvicorn` for `/docs` testing.
2. The later chat change depends on `require_session` from here; no migration of data needed.
3. Rollback: remove the package mount; nothing else depends on it yet.

## Open Questions

- None that change specs or tasks. The trusted client-IP source for rate limiting is answered in the deploy change, not here.
