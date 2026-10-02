# Design

## Context

See proposal.md (Why). The repo runs one FastAPI process that must serve the demo page and, later, the same service; policy, session and idempotency live in code and no orchestrator ever sees `customer_id`. At the time of this change two apps coexisted in `sentinel-ai-core`: the documented `uvicorn app.main:app` started the production track (direct LLM call, no policy, identifiers in the payload), while `create_app()` held the real architecture and was never served. `sentinel-login/` still shipped a typed reply contract (`app/chat/contract.py`) that the served app did not use.

## Goals / Non-Goals

**Goals:**
- One served app and one versioned API under `/api/v1` that the demo and the later service share.
- A typed, strict reply contract the page can render without guessing.
- Gold reachable through the real DuckDB view behind the existing seam, with a labeled fallback.

**Non-Goals:**
- Advisor queue and admin panel (pending decision 29; later change).
- A SQLite/Postgres dispute adapter, a real LLM by default, retiring `sentinel-login/`.
- Changing the orchestrator or the policy engine.

## Decisions

**1. `create_app()` becomes the only app; production routers are deleted, not toggled.** `app.main:app = create_app()` and the production `/api/v1/chat`, `/api/v1/disputes`, `/api/v1/transactions?session_id=` routes plus `auth_compat.py` are removed outright. Alternative considered: keep both behind an env flag; rejected — a switch preserves the two contracts that drifted in the first place, and a deleted route returns 404 where a disabled one returns 500-shaped surprises. `db/` and `models/` stay in the tree unmounted, as a future SQLite dispute adapter, instead of being deleted with the routers.

**2. Everything moves under `/api/v1` in one breaking commit.** `session/{login,logout,me}`, `transactions`, `chat`, `health`; `/chat`, `/transactions`, `/session/*` and `/auth/*` disappear. The same commit updates `app/static/app.js`, every test and `eval/runner.py`, so no consumer is left on an old path. The page and the runner are in-repo, which makes a coordinated break cheaper than a deprecation window.

**3. Strict typed variants in `app/schemas/chat.py`.** Exactly one of `text`, `clarification`, `confirm_box`, `case_confirmation`, `handoff`, `error`, modeled after `sentinel-login/app/chat/contract.py` and trimmed to the specs: raw values plus translation keys, no authored prose; `error` carries a generic key plus `trace_id`. Alternatives: free-form strings with a `type` field (rejected — untestable, the browser had already broken once); JSON Schema instead of Pydantic (rejected — the repo already standardizes on Pydantic models).

**4. Identity comes only from the HttpOnly session cookie.** The chat body accepts `message` and `selected_reference` and nothing else (422 before business logic); `GET /api/v1/session/me` returns role and country, never `customer_id`. This is how "no orchestrator sees `customer_id`" is enforced at the edge rather than trusted from the caller.

**5. Gold adapter behind the existing seam with startup probe.** `app/tools/gold_duckdb.py` reads the PII-free view `v_service_dispute_eligible_transactions`; `SENTINEL_GOLD_SOURCE` (`auto`/`mock`/`duckdb`) selects, `auto` probes the view at startup and falls back to the mock, and `GET /api/v1/health` reports the active source so the demo state is observable. Alternative: fail hard without the view; rejected — the demo must run on a laptop without the pipeline output.

**6. The handoff package is written to the closing turn record.** The same package returned in the `handoff` variant (request, verified facts, actions, evidence, open questions, language, country — no `customer_id`, no raw text) is stored on the turn's observability record, so the log and the reply cannot disagree.

## Risks / Trade-offs

- [Breaking every API path at once] → page, tests, runner and routes change in one commit; `test_old_paths_are_gone` pins the 404s.
- [DuckDB view missing or unreadable at startup] → `auto` falls back to the mock and health reports `mock`; no crash.
- [Stricter contract than the old replies] → contract tests assert every variant; the browser's confirmation card is covered by `tests/test_ui.py`.
- [Unmounted `db/`, `models/` look like dead code] → kept deliberately for the dispute adapter (see proposal Impact); noted here so a later cleanup does not delete them prematurely.

## Migration Plan

Single commit: routers and schemas first, then page, tests and runner, then evidence runs frozen as new folders (`evidence/evaluation-runs/2024Q4-eval-v3/`, `evidence/adversarial/20261001T114008Z/`). Rollback is `git revert` of that commit; evidence runs are write-once and stay valid either way.
