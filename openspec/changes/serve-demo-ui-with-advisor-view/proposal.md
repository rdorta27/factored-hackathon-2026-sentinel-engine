# Proposal

## Why

`sentinel-login/` was a second backend (auth, chat, disputes, Gold, advisor queue, admin) beside `sentinel-ai-core/`, which now serves the only API and produces a structured handoff ticket that no human could read. The brief asks to give the human agent the request, verified facts, actions taken, evidence and open questions (REQ-0008, P0), with roles enforced in code (REQ-0007, P0) and a simple frontend (REQ-0038, P0). Pending decision 29 is closed by [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md); this does not contradict [006](../../../docs/build/decisions/006-frontend.md): still one page served by the same FastAPI process.

## What Changes

- **BREAKING**: login moves to `/api/v1/auth/{login,logout,me}` (the versioned path from PR #20); `/api/v1/session/*` is removed. A password is always required.
- `SENTINEL_DEMO_AUTH=1` loads the documented false advisor user (`ADV-0001`); without it only customers exist.
- New `GET /api/v1/handoffs` and `GET /api/v1/handoffs/{id}`, role `advisor`: the full package (summary, per-turn conversation, verified facts, actions attempted, evidence, open questions) plus customer id and country. Customers get 403 and `access_denied`.
- Customer endpoints (chat, transactions, disputes) require role `customer`.
- The ai-core page lands each role on its view: chat for customers, a read-only ticket view for the advisor; the chat renders a handoff card.
- A handoff whose escalating turn names no charge carries the last charge verified earlier in the session.
- `sentinel-login/` keeps only its original page as a reference; backend, tests and packaging are removed. The admin panel is not migrated.

## Capabilities

### Modified Capabilities

- `session`: auth paths, roles and the demo flag.
- `roles`: customer and advisor enforced; advisor reads tickets read-only; admin observability removed from scope.
- `chat-ui`: role landing without the admin panel.

## Impact

- `sentinel-ai-core/app/`: `session/router.py` (`require_role`), `session/store.py` (demo roles), `session/fixtures/users.json` (advisor), new `routers/handoffs.py`, `state/cases.py` (`handoffs()`), `schemas/chat.py` (`AdvisorTicket`), `static/` (role landing, advisor view, handoff card), `main.py`.
- Tests: `tests/test_handoffs_api.py`; adversarial B11, B12; paths in every test and `eval/runner.py`.
- `sentinel-login/`: only `README.md` and `app/ui/` remain.

## Non-goals

- Advisor actions (claim, state change), routing by language and specialty (REQ-0046, P2), the admin panel.
- Login by customer number alone.
