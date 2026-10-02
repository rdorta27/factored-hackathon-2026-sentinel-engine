# Design

## Context

See proposal.md (Why). Sessions, conversation state and cases lived in process memory: a restart dropped them and a second worker answered 401 mid-conversation. The chat already runs a full turn cycle (policy decision, confirm box, idempotency, read-back, closing turn record) but only inside `demo_chat`; the PR #20 disputes endpoints used SQLite without that cycle, and handoffs were logged but never filed. Constraints from context: one FastAPI process, policy and idempotency in code, no `customer_id` to the orchestrator, repo delivered public so no data or credentials in the tree.

## Goals / Non-Goals

**Goals:**
- State survives a restart and a second worker, with retention rules that keep PII out of the repo and out of stale rows.
- One open dispute per charge regardless of session or entry point, and handoffs filed as advisor-readable tickets.
- The REST dispute API runs the same turn cycle as the chat — one code path, one policy.

**Non-Goals:**
- Postgres, multi-instance deployment, shared login-attempt counters.
- Policy threshold work (decisions 25–27, separate change).
- A "my cases" panel or advisor queue UI.

## Decisions

**1. Sync SQLAlchemy 2.x over stdlib `sqlite3`, selected by `SENTINEL_STATE_BACKEND`.** `sqlite` is the default, `memory` stays for tests and the offline eval. Alternatives considered: async SQLAlchemy + aiosqlite (rejected — routes are I/O-light and sync keeps the turn cycle readable; async would spread `await` through the policy and case code for no measured gain); Postgres now (rejected — a URL change later is cheap, and the demo must run on a laptop with no service to install). The PR #20 models are reused and extended rather than replaced.

**2. Repositories behind `Protocol`s, memory implementation kept.** `SessionStore`, `CaseRepository`, conversation store each have an in-memory and a SQLite implementation (`app/state/`, `app/session/store.py`). The memory backend is not dead code: it is what the eval runner and fast unit tests use, and it is the rollback switch.

**3. Rows are keyed by a hash of the session token; retention is delete-on-exit.** `sha256(token)` (never the raw token) keys session and conversation rows; logout and expiry delete the conversation, and login purges orphans from dead sessions. Alternative: TTL sweeps in the background (rejected — a cron-like loop in a demo process is another failure mode; deleting at the exit points covers the cases the specs name). Login attempt counters stay in memory, documented as per-process, because they are rate limiting, not conversation data.

**4. Idempotency scope is an opaque salted hash of the customer, not the session token.** That makes "one open dispute per charge" hold across sessions and entry points: a charge with an open case is also marked disputed for the policy, so a second session gets a refusal instead of a second case. Alternative: unique index on charge alone (rejected — different customers can hold charges with the same display reference across countries; the scope must include the customer).

**5. Handoffs are filed as cases (`kind=handoff`, `status=Escalated`) carrying the package.** The advisor ticket is a row, not a log line, so `GET /api/v1/handoffs` is a query and the package survives restarts. The package holds conversation summary and every attempted action; verified facts gate what replies may show.

**6. The REST API reuses the chat's turn cycle.** `POST /api/v1/disputes/preview` computes the policy decision with no write; `POST /api/v1/disputes` opens only the previewed charge and returns 409 `preview_required` otherwise; `GET` and `GET /{case_id}` list the caller's own cases with no `customer_id` anywhere. Alternative: a lighter direct-create endpoint (rejected — the PR #20 endpoints failed exactly there: no confirmation, no policy, no idempotency; two paths would drift again).

## Risks / Trade-offs

- [SQLite write contention if the demo scales out] → single-process by design; WAL pragmas on the engine; Postgres is a URL change if that changes.
- [Delete-on-logout destroys evidence a user might want] → the closing turn record keeps the aggregates; the retention rule is the PII requirement, not a bug.
- [Salted customer hash rotates if the salt changes] → salt lives in `.env`, documented as stable for the demo lifetime.
- [Two entry points (chat, REST) could diverge] → both call the same turn-cycle function; `test_disputes_api.py` and the chat tests assert the same outcomes.

## Migration Plan

Default flips from memory to SQLite in one commit together with the models and stores; tests keep `memory`. Rollback is `SENTINEL_STATE_BACKEND=memory`. Evidence freezes as new write-once folders (`evidence/evaluation-runs/2024Q4-eval-v4/`, `evidence/adversarial/20261001T122759Z/`); the adversarial set grows to 34 attacks (B9, B10, C6, D6, D7) and C4 now asserts logout deletes the thread.
