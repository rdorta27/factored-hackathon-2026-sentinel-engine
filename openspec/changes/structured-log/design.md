# Design

## Context

`trace_id` already exists per request (`main.py` middleware, `secrets.token_hex(8)`) and reaches `routers/chat.py` via `request.state`. `AuditLogger` (`app/session/audit.py`) logs only auth events with cleartext `customer_id` and IP. `Ports` (`app/orchestrator/step.py`) carries `session_ref` (today a raw token prefix also used in the idempotency key), `tools`, `model`, `country`, `today`. `ModelPort` reports no tokens or cost, so fakes emit constants. No `app/observability/` package exists; `.gitignore` covers `.local/` but not `var/`.

## Goals / Non-Goals

Goals: one record per step plus a closing record per turn, joinable by `trace_id` and replayable from a file; zero personal data by construction; no changes to engine signatures beyond optional `Ports` fields.
Non-goals: timeout instrumentation (no timeout plumbing exists), `trace_id` in success payloads, centralized sinks.

## Decisions

- **Extend `Ports` with optional `trace_id` and `observer` (default `None` = no-op)** over an implicit `ContextVar`: explicit, testable, and no existing caller or test breaks. Deviation from the local task note ("don't touch `ports.py`") recorded here. See `docs/architecture/specification.md`, Observability section.
- **Single record dataclass with `step` including `session` and `turn`** over separate classes: one schema, one writer, auth events ride the same pipeline.
- **`session_ref = sha256(salt + session_id)` truncated to 16 hex chars**; salt from `SENTINEL_SESSION_SALT`, ephemeral plus a startup warning when unset, never persisted beside the logs. Precaution: `session_ref` also seeds the dispute idempotency key, so its value changes with the salt scheme within the demo only.
- **Map `ToolStatus.NOT_FOUND` to outcome `failed`; reserve `timeout`** as a declared limitation. `model: "fake"`, `route: "mock"`, `prompt_version: "none"`, zero tokens and cost while fakes serve; fields never empty so the runner never branches on nulls.
- **Migrate, don't parallel-run, `AuditLogger`**: auth events become `step: session` records through the same writer; `test_session.py` assertions move to the new shape in the same change.
- **Refunded fix via the existing candidate adapter** in `GET /transactions` (the path chat already uses), unmarking the 2 strict xfails rather than adding a parallel mapping.

## Risks / Trade-offs

- [Risk] Another change touches `routers/chat.py` and duplicates `trace_id` generation → Mitigation: reuse `request.state.trace_id` from the middleware; never generate in the router.
- [Risk] Extra fields become PII surface → Mitigation: the 16 spec fields are closed; anything else needs a spec delta first.
- [Risk] `session.token[:12]` usages outside logging assume the old format → Mitigation: grep for `session_ref`/`token[:12]` during implementation; idempotency keys stay valid within the demo.
- [Risk] JSONL grows unbounded locally → Mitigation: demo/evaluation volume is hundreds of turns; rotation is a production concern.

## Migration Plan

Single change, no rollout steps: new package plus edits, all tests green, one commit per task. Rollback is `git revert` per task commit.

## Open Questions

None that change specs, approach, or tasks.
