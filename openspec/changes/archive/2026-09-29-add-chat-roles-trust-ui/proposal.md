# Proposal: add-chat-roles-trust-ui

## Why

Login exists but the product does not: there is no chat, no roles, and no interface. Mentor feedback sets the bar higher than "case opened": a customer with a surprise charge needs visible evidence (verified receipt, timeline, handoff reference) or they will call a human anyway. This change delivers the full mock-backed demo loop that earns that trust.

## What Changes

- `POST /chat` (role `customer`): body carries only `message` (`extra="forbid"`); `customer_id` comes from the session. Reuses `require_session` from the `sentinel-login` change.
- Structured response contract (Pydantic module shared later with the real orchestrator): `text`, `clarification`, `case_confirmation` (with `verified=true` only after re-read), `handoff`, `error` (generic message plus `trace_id`).
- Verify-before-claim rule: `case_confirmation` is emitted only if the case was re-read from the store after creation; otherwise bounded retries, then `handoff`. The words "resolved" and "registered" are never interchangeable.
- Minimal server-side RBAC: roles `customer`, `advisor`, `admin` stored in the session; `require_role(...)` dependency per endpoint; role failures return 403 plus `access_denied` audit. Mock users for all three roles with documented demo credentials.
- Advisor queue: escalated handoffs listed with the structured summary (request, verified facts, actions, evidence, open questions); advisor can claim a case and change its state. Advisor sees only case-necessary fields, never the full profile.
- Admin read-only view: audit log plus basic counts (logins, failures, lockouts, handoffs, denied access). No full conversations.
- Same-process frontend (vanilla HTML/CSS/JS, no frameworks or CDNs): role-based landing (chat, queue, panel), receipt card with verified check and timeline, always-visible "talk to an agent" button, masked sensitive data (`****1234`), `textContent`-only rendering, light/dark theme via CSS variables with localStorage preference only, i18n JSON files (`es-419` base, `es-MX`/`es-CO`/`es-AR` overrides, `pt-BR`) with fallback to `es-419`.
- Mock orchestrator behind an `Orchestrator` protocol with 4 demo scenarios: normal (verified confirmation), ambiguous (`clarification`), high-risk (`handoff` visible in the advisor queue), failed verification (retry then `handoff`).

## Capabilities

### New Capabilities

- `chat`: `POST /chat`, structured response contract, verify-before-claim rule, mock orchestrator scenarios.
- `roles`: session roles, `require_role`, advisor queue with claim/state change, admin read-only audit and metrics.
- `chat-ui`: role-based pages, receipt card and timeline, agent button, masking, themes, i18n with fallback, XSS-safe rendering.

### Modified Capabilities

- None (no archived specs exist yet).

## Impact

- Code lives in `sentinel-login/` reusing its package, pytest config, session seam, and audit logger; no new runtime dependencies (stdlib plus FastAPI/Pydantic v2 only).
- New endpoints: `POST /chat`, advisor queue endpoints, admin endpoints; new static frontend served by the same process per `docs/build/decisions/006-frontend.md`.
- Extends the session with a `role` field (additive; existing login tests keep passing).
- Traces to REQ-0001, REQ-0002, REQ-0003, REQ-0005, REQ-0006, REQ-0008, REQ-0009, REQ-0010, REQ-0011, REQ-0012, REQ-0021, REQ-0026, REQ-0027, REQ-0032, REQ-0038, REQ-0039, REQ-0040, REQ-0041, REQ-0044, REQ-0047; builds on `docs/build/security.md`, `docs/build/conversation.md`, and decisions 005/006.

## Non-goals

- Phase 2 replacements (real orchestrator, Gold tables) are a later change; this change only defines the `Protocol` seams and documents mock vs real.
- No real money movement or live decisions (REQ-0004): all actions simulated.
- No dashboard beyond the read-only admin counts (decision scope: no dashboard).
- No multi-worker session sharing, no payload-size middleware, no CSRF hardening beyond the current `SameSite=Lax` posture; each stays a documented limit.
