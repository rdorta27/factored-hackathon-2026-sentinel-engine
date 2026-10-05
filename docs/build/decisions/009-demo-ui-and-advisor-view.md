---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 009 · Demo UI with role landing and advisor view, served by ai-core

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 29 with option (a), without the admin panel.

## Context

`sentinel-login/` started as a mock backend with its own auth, chat, disputes, Gold store, advisor queue and admin panel, and a page with role landing. `sentinel-ai-core/` now serves the only API (`/api/v1`), the chat page, persistent cases and a structured handoff package. Two backends for one demo contradict [005](005-backend.md). They also give the advisor no place to read the ticket that the system makes.

The brief asks to "provide the human agent with the request, verified facts, actions taken, supporting evidence, and unresolved questions" (REQ-0008, P0). The mentor review (Factored, 9/30) adds: the advisor must see why the case came to them. Code must enforce the roles (REQ-0007, P0). Advisor routing is REQ-0046 (P2). REQ-0038 (P0) asks for a simple frontend and excludes a dashboard.

## Options

1. **Keep `sentinel-login/` as a second backend.** No work now. Two auth stacks, two contracts, two processes to deploy.
2. **Serve the `sentinel-login/` page from ai-core.** It brings role landing. But the page has no confirm box (REQ-0006). It shows a receipt, a queue status and an SLA date that the chat contract removed, and the name of the customer.
3. **Keep the ai-core page and add role landing and an advisor view to it.** The view reads `GET /api/v1/handoffs`. `sentinel-login/` keeps only its original page as a reference.

## Decision

Option 3. One process, one page, one API:

- Login is always `POST /api/v1/auth/login` with `login` and a password. `SENTINEL_DEMO_AUTH=1` enables the documented false advisor credential. Without it, only customers exist. No login by customer number alone (brief: "a customer number alone does not prove identity"; REQ-0027).
- The advisor reads escalated tickets at `GET /api/v1/handoffs` and `GET /api/v1/handoffs/{id}`, role `advisor` only. A ticket shows the reason, the verified facts, a summary of the conversation, the actions attempted, the open questions, and the customer id and country. No names, no profile. A customer gets 403 and an `access_denied` audit record.
- The customer endpoints (chat, transactions, disputes) require the role `customer`.
- The admin panel and audit views stay out. REQ-0038 excludes dashboards, and the structured log covers REQ-0025 and REQ-0029.
- `sentinel-login/` loses its backend (auth, chat, disputes, Gold, customer, advisor, admin, audit, tests, packaging). Its page stays as the original demo UI for reference. The service does not serve it.

This does not contradict [006](006-frontend.md). The frontend is still one page of HTML and a little JavaScript, served by the same FastAPI process. The page now has a second view for the advisor role.

## Consequences

- One login, one API, one deploy. The advisor sees the ticket that the chat makes, so the video can show the human in the loop.
- The advisor view is read-only: no claim and no change of state. The old queue actions of `sentinel-login` are not migrated.
- The login path moves from `/api/v1/session/*` to `/api/v1/auth/*`. The tests, the eval runner and the docs follow.
- Open: routing by language and specialty (REQ-0046), the admin panel, and the removal of the reference page in `sentinel-login/` when nobody uses it.
- *Updated 10/5:* the `sentinel-login/` folder is removed. Nothing served it, imported it or tested it, and it confused readers of the repository (REQ-0034). The history stays in Git and in `openspec/changes/archive/`.
- *Updated 10/4:* PR #57 adds the product interface and the advisor trace of each step (REQ-0029, REQ-0038). Screens: [`docs/build/screenshots/ui-product/`](../screenshots/ui-product/).
