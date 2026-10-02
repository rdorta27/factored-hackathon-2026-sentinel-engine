# Proposal

## Why

Sessions, conversation state and cases lived in process memory: a restart lost them and a second worker answered 401 mid-conversation. The Factored mentor review recommended externalizing conversation state and isolating the action executor. Two gaps followed from the in-memory design: the idempotency key was scoped to the session token, so a new session could open a second dispute on the same charge, and handoffs were not filed anywhere. The PR #20 disputes endpoints (SQLite) had no confirmation, no policy and no idempotency, and no route created their sessions (REQ-0004, REQ-0005, REQ-0006, REQ-0008, REQ-0026, REQ-0027; [004](../../../docs/build/decisions/004-pii-lifecycle.md), [005](../../../docs/build/decisions/005-backend.md)).

## What Changes

- Sessions, conversation state and cases persist in SQLite (`SENTINEL_STATE_BACKEND=sqlite`, default; `memory` for tests and the offline eval). The PR #20 models are reused and extended; Postgres later is a URL change. Login attempts stay in memory (documented: per process).
- Conversation state, including customer turns, is deleted on logout and on expiry; orphaned rows are purged on login. Rows are keyed by a hash of the session token.
- One open dispute per charge across sessions and entry points: the idempotency scope is an opaque hash of the customer, and charges with an open case are marked disputed for the policy.
- Handoffs are filed as cases (`kind=handoff`, `status=Escalated`) with their package: the advisor ticket.
- New `/api/v1/disputes`: `POST /preview` (policy decision, no write), `POST` (opens only the previewed charge; 409 otherwise), `GET` and `GET /{case_id}` (own cases, no `customer_id`). Both POSTs run the chat's turn cycle: same policy, confirm box, idempotency, read-back and turn record.

## Capabilities

### Modified Capabilities

- `disputes`: two-step API, case listing, one open dispute per charge.
- `session`: persistent sessions and conversation retention.
- `chat`: handoffs filed as tickets.

## Impact

- `sentinel-ai-core/app/`: `db/session.py` (sync engine), `models/` (extended + `conversation.py`), new `state/`, `session/store.py` (`SqliteSessionStore`), `session/router.py`, `tools/bound.py`, `routers/demo_chat.py` (shared turn cycle), new `routers/disputes.py`, `schemas/chat.py`, `main.py`, `eval/runner.py` (memory backend).
- Adversarial set grows to 34 attacks (B9, B10, C6, D6, D7); C4 now asserts logout deletes the thread.
- Evidence: `evidence/evaluation-runs/2024Q4-eval-v4/`, `evidence/adversarial/20261001T122759Z/`.

## Non-goals

- Policy thresholds (decisions 25–27): separate branch.
- Postgres, multi-instance deployment, shared login-attempt counters.
- A "my cases" panel in the chat page; advisor queue UI.
