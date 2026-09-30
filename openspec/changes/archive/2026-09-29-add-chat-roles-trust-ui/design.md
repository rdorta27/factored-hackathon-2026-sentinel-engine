# Design: add-chat-roles-trust-ui

## Context

See proposal.md (Why). Current state: `sentinel-login/` (change `sentinel-login`, complete) provides opaque sessions, `require_session`, JSON-lines audit with `trace_id`, and PBKDF2 mock users. This change adds roles to the session, the chat endpoint with a mock orchestrator, and the same-process UI. Constraints: Python 3.12, FastAPI + Pydantic v2, no new runtime libs; English code; work inside `sentinel-login/` with its pytest config.

## Goals / Non-Goals

**Goals:**

- Phase 1 fully demoable with mocks; Phase 2 swaps adapters only.
- Every trust claim on screen (verified check, timeline, handoff reference) backed by a store read or an audit event.

**Non-Goals:**

- Real orchestrator/LLM wiring, Gold reads, and multi-worker sessions stay out; the `Protocol` seams and the documented limits are the deliverable for Phase 2.

## Decisions

- **Role in session, `require_role` dependency.** Role rides the existing opaque session (one additive field), checked by a `require_role(...)` dependency mirroring `require_session`. Server-side check means a forged frontend grants nothing; 403 plus `access_denied` audit. Alternative rejected: frontend-only gating.
- **Response contract as its own Pydantic module.** One discriminated set (`text`, `clarification`, `case_confirmation`, `handoff`, `error`) owned by `app/chat/contract.py`, imported by both the mock orchestrator and the endpoint. Phase 2 keeps the module untouched; only the orchestrator adapter changes. Alternative rejected: dicts passed through layers.
- **Verify-before-claim in code, not in prompt.** The endpoint re-reads the case from the `CaseStore` protocol after creation and compares identifiers before emitting `verified=true`; mismatch or read failure goes to bounded retry then `handoff`. This is the direct answer to the mentor's "$1,000 surprise charge" test. Alternative rejected: trusting the orchestrator's word.
- **Mock orchestrator as a scenario switch, not fake AI.** Deterministic keyword routing over four scenarios keeps the demo reproducible (REQ-0028) and doubles as the keyword baseline the ML comparison needs. Alternative rejected: calling any real model in Phase 1.
- **Advisor sees case slices, admin sees counts.** Queue returns the handoff summary projection (no transcript, no profile); admin returns audit aggregates (no message text). Minimum privilege falls out of the projections, not out of caller discipline. Alternative rejected: full objects filtered in the frontend.
- **Vanilla frontend, static files, no CDN.** Same-process HTML/CSS/JS per decision 006 keeps Thursday's deploy to one process and removes supply-chain risk for the demo. Rendering uses `textContent` only; theme via CSS variables with `prefers-color-scheme` default; only the theme key touches `localStorage`. Alternative rejected: htmx/React/CDN styling.
- **i18n as layered JSON.** `es-419` base dictionary, regional files with only overrides, `pt-BR` full file, server-side fallback lookup (`es-AR` miss → `es-419`). Keeps translators' diff tiny and matches `docs/build/conversation.md` language strategy. Alternative rejected: one file per locale with duplication.
- **No new dependencies.** Mocks, queue, metrics, and i18n are stdlib plus FastAPI/Pydantic. `pytest`/`httpx` already cover `TestClient`.

## Risks / Trade-offs

- [Risk] Scope is large for one change → Mitigation: ordered task groups (customer + chat + contract, then advisor, then admin/themes/i18n); each group lands its own tests.
- [Risk] In-memory queue/cases vanish on restart → Mitigation: documented demo limit; `CaseStore` protocol is the Phase 2 swap point.
- [Risk] Mock keyword routing might look like "the AI" → Mitigation: every mock response path labeled mock-sourced; demo script states Phase 1 uses no model.
- [Risk] Session `role` extension touches login code → Mitigation: additive field with default; existing 26 login tests must stay green.
- [Risk] CSRF residual from cookie transport (carried over) → Mitigation: unchanged posture (`SameSite=Lax`, same-origin JSON); hardening stays a documented later item.

## Migration Plan

1. Land Phase 1; demo runs on one `uvicorn` process (`workers=1`).
2. Phase 2 change replaces `MockOrchestrator` and `InMemoryCaseStore` adapters; contract, endpoints, and frontend unchanged.
3. Rollback: unmount chat/UI routers; login keeps working standalone.

## Open Questions

- None that change specs or tasks. The trusted client-IP source and shared session store are owned by the deploy change.
