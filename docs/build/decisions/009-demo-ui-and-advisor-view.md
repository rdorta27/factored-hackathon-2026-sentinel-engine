# 009 · Demo UI with role landing and advisor view, served by ai-core

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 29 with option (a), without the admin panel.

## Context

`sentinel-login/` started as a mock backend with its own auth, chat, disputes, Gold store, advisor queue and admin panel, plus a page with role landing. `sentinel-ai-core/` now serves the only API (`/api/v1`), the chat page, persistent cases and a structured handoff package. Two backends for one demo contradict [005](005-backend.md) and leave the advisor without a place to read the ticket the system produces.

The brief asks to "provide the human agent with the request, verified facts, actions taken, supporting evidence, and unresolved questions" (REQ-0008, P0). The mentor review (Factored, 9/30) adds: the advisor must see why the case reached them. Roles must be enforced in code (REQ-0007, P0); the advisor routing is REQ-0046 (P2). REQ-0038 (P0) asks for a simple frontend and scopes out a dashboard.

## Options

1. **Keep `sentinel-login/` as a second backend.** No work now; two auth stacks, two contracts, two processes to deploy.
2. **Serve the `sentinel-login/` page from ai-core.** Brings role landing, but the page lacks the confirm box (REQ-0006) and renders a receipt, queue status and SLA date that the chat contract removed, plus the customer's name.
3. **Keep the ai-core page and add role landing and an advisor view to it**, reading `GET /api/v1/handoffs`; `sentinel-login/` keeps only its original page as a reference.

## Decision

Option 3. One process, one page, one API:

- Login is `POST /api/v1/auth/login` with `login` and a password, always. `SENTINEL_DEMO_AUTH=1` enables the documented false advisor credential; without it only customers exist. No login by customer number alone (brief: "a customer number alone does not prove identity"; REQ-0027).
- The advisor reads escalated tickets at `GET /api/v1/handoffs` and `GET /api/v1/handoffs/{id}`, role `advisor` only: reason, verified facts, conversation summary, actions attempted, open questions, and the customer id and country. No names, no profile. Customers get 403 and an `access_denied` audit record.
- Customer endpoints (chat, transactions, disputes) require role `customer`.
- The admin panel and audit views stay out: REQ-0038 scopes out dashboards and REQ-0025/REQ-0029 are covered by the structured log.
- `sentinel-login/` loses its backend (auth, chat, disputes, Gold, customer, advisor, admin, audit, tests, packaging). Its page stays as the original demo UI for reference; it is not served.

This does not contradict [006](006-frontend.md): the frontend is still one page of HTML and a little JavaScript served by the same FastAPI process. The page now has a second view for the advisor role.

## Consequences

- One login, one API, one deploy; the advisor sees the ticket the chat produces, which makes the human-in-the-loop visible in the video.
- The advisor view is read-only: no claim or state change (the old `sentinel-login` queue actions are not migrated).
- The login path moves from `/api/v1/session/*` to `/api/v1/auth/*`; tests, the eval runner and docs follow.
- Pending: routing by language and specialty (REQ-0046), the admin panel, and retiring the reference page in `sentinel-login/` once nobody uses it.
