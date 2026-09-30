# Proposal

## Why

`sentinel-login/` and `sentinel-ai-core/` both define `POST /chat`, with different bodies and different rules for opening a dispute. The submission path must be one FastAPI process: the loop and policy engine already in `sentinel-ai-core/`, with the test session and customer chat adapted to that contract (REQ-0006, REQ-0027).

## What Changes

- Add a test session under `app/session/`. Identity comes only from the session. `customer_id` is bound on the tool port before the loop runs ([005](../../../docs/build/decisions/005-backend.md), REQ-0047).
- **BREAKING** for the login chat: adopt its `ChatRequest` (`message` plus `selected_reference`) and rewire the handler to `step()` and the policy engine. An exact match or a tap no longer opens a dispute.
- `selected_reference` is selection when no confirm box is pending, and confirmation when it matches the pending box. The `confirmation_token` is issued in code and is not a client field (REQ-0006).
- Keep `clarification` (with candidates) and verified `case_confirmation`. Add `confirm_box`. A case number is reported only after read-back (REQ-0003, REQ-0005).
- Use deterministic grounding as the Understand fake. It does not decide. Pending, Reversed, Declined, window, person, fraud, and amount still win (REQ-0048).
- The session reads `SENTINEL_REFERENCE_DATE` (default `2026-06-17`) once at startup and injects it as the engine's demo date. The engine does not read the clock. Chat does not restate that requirement.
- Serve the customer chat from `app/static/` ([006](../../../docs/build/decisions/006-frontend.md)): receipt without a download route, chips, transaction panel, locales, branding read-only, masking, confirm box.
- Add session-scoped `GET /transactions`. Do not keep `/api/v1/transactions`.
- Document that only `sentinel-ai-core` is the submission server. Leave `sentinel-login/` in place until a later cleanup.

## Capabilities

### New Capabilities

- `session`: opaque test session, expiry, revocation, lockout, audit without secrets, and the reference date.

### Modified Capabilities

- `chat`: one `POST /chat` contract; selection is not an open; `confirm_box` added; verified confirmation kept.
- `dispute-confirmation`: confirmation turn is `selected_reference` only while a box is pending; no SLA receipt route.
- `orchestrator-loop`: grounding selects the candidate; the structured id has two meanings by state.
- `chat-ui`: customer surfaces only; agent control is two-step. Role landing, the advisor queue, and the admin panel are deferred, tracked in pending decision 29.
- `gold-layer`: listing is `GET /transactions`, session-scoped; `GoldTransactions` signatures unchanged.

## Impact

- New HTTP surface in `sentinel-ai-core`: session routes, `POST /chat`, `GET /transactions`, and the static chat.
- The loop stops taking the first candidate. Gold reads stay behind the existing tool port.
- `sentinel-login/` is not deleted and is not the submission server.
- Personal data follows option 2 of [004](../../../docs/build/decisions/004-pii-lifecycle.md): session isolation, no token vault.

## Non-goals

- Retiring `sentinel-login/`, real Gold, a real LLM, LangGraph, a token vault, and `DisputePolicy`, `DisputeService`, `sla`, or `MockOrchestrator` as the decider.
- Role landing, the advisor queue, and the admin panel. Deferred, tracked in pending decision 29.
- Editing `docs/build/flows/data-evidence.md` or `options.md`.
- Preserving `/auth/*`, `/api/v1/disputes/*`, `/advisor/*`, or `/admin/*`.
