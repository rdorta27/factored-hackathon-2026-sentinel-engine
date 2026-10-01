# Proposal

## Why

`sentinel-ai-core/app/main.py` served two apps. The documented command (`uvicorn app.main:app`) started the production track: `/api/v1/chat` called the LLM directly, skipped the orchestrator and the policy engine, sent transaction ids to the model and returned `customer_id` to the browser, and no route created its sessions. The demo app (`create_app()`) had the real architecture but was not served, and its chat replies did not match what the page renders: the confirmation card threw in the browser. Specs also disagreed (`auth-login` vs `session`, `disputes` Proof-of-Work vs `chat` "no SLA, queue or receipt"). The submission needs one API that the hackathon demo and the later service share (REQ-0007, REQ-0008, REQ-0027, REQ-0033, REQ-0038, REQ-0047, REQ-0048; [005](../../../docs/build/decisions/005-backend.md), [006](../../../docs/build/decisions/006-frontend.md)).

## What Changes

- **BREAKING**: one app, `app.main:app = create_app()`. Every API route moves under `/api/v1`: `session/{login,logout,me}`, `transactions`, `chat`, `health`. `/chat`, `/transactions`, `/session/*`, `/auth/*`, `/api/v1/auth/*` and the production `/api/v1/chat`, `/api/v1/disputes`, `/api/v1/transactions?session_id=` are removed.
- The session stays an HttpOnly cookie. `GET /api/v1/session/me` returns role and country, not `customer_id`.
- Chat replies are typed models (`app/schemas/chat.py`) based on `sentinel-login/app/chat/contract.py`, trimmed to the spec. `handoff` carries the advisor package (request, verified facts, actions taken, evidence, open questions, language, country), without `customer_id` or raw text. The same package is written to the closing turn record.
- Gold real behind the existing seam: a DuckDB adapter over `v_service_dispute_eligible_transactions`, with fallback to the mock (`SENTINEL_GOLD_SOURCE`).
- Disputes are created only through the chat confirm box. No REST create, no Proof-of-Work receipt.

## Capabilities

### Modified Capabilities

- `chat`: path, typed variants, handoff package.
- `session`: paths, `me` without the identifier.
- `gold-layer`: listing path and shape; DuckDB adapter with fallback replaces "real deferred".
- `disputes`: REST creation, Proof-of-Work and receipt deadline removed; chat delegation kept.
- `auth-login`: removed, superseded by `session`.
- `observability`: closing record carries the handoff package.
- `evaluation-runner`: replays `POST /api/v1/chat`.

## Impact

- `sentinel-ai-core/app/`: `main.py`, `routers/demo_chat.py`, `routers/demo_transactions.py`, `session/router.py`, `schemas/chat.py`, `observability/`, new `tools/gold_duckdb.py`; production routers and `auth_compat.py` deleted; `db/` and `models/` kept unmounted as a future SQLite dispute adapter.
- `app/static/app.js` paths; i18n keys; tests and `eval/runner.py` paths.
- New evidence runs: `evidence/evaluation-runs/2024Q4-eval-v3/`, `evidence/adversarial/20261001T114008Z/`.

## Non-goals

- Advisor queue and admin panel (`roles`, `chat-ui` role landing): still deferred, pending decision 29; optional if time allows.
- A SQLite or Postgres dispute adapter, a real LLM by default, retiring `sentinel-login/`.
- Changing the orchestrator or the policy engine.
