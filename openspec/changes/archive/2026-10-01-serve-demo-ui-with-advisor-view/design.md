# Design

## Context

See proposal.md (Why). `sentinel-ai-core/` now serves the only API and produces a structured handoff package, but no human could read it, and `sentinel-login/` was still a second backend beside it. Decision [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md) closed pending decision 29: one page served by the same FastAPI process, roles enforced in code, advisor sees a read-only ticket. Constraints: no framework on the frontend, roles never delegated to the orchestrator, repo delivered public so the demo advisor is a documented fixture, not a credential.

## Goals / Non-Goals

**Goals:**
- An advisor can read a handoff ticket — summary, conversation, verified facts, actions, evidence, open questions — through the served page.
- Roles enforced in code on every route, with the demo advisor gated behind an explicit flag.
- One backend: `sentinel-login/` reduced to its original reference page.

**Non-Goals:**
- Advisor actions (claim, state change), routing by language and specialty (REQ-0046), the admin panel.
- Login by customer number alone.

## Decisions

**1. Auth paths move to `/api/v1/auth/{login,logout,me}`; password always required.** The versioned path matches PR #20's surface, so there is one auth API under one prefix, and `/api/v1/session/*` is removed in the same commit that updates tests, `app.js` and `eval/runner.py`. Alternative: keep `/session/*` (rejected — two names for one thing, and the versioned path is what the rest of the API uses).

**2. Roles enforced by a FastAPI dependency, `require_role`, exported as `require_customer` / `require_advisor`.** The stored role on the live session decides; a mismatch returns 403 and emits `access_denied` to the audit log. Alternatives: middleware keyed on path prefixes (rejected — implicit, easy to miss a new route); role checks in the orchestrator (rejected — context rule: policy in code, orchestrator never sees identity).

**3. Demo advisor behind `SENTINEL_DEMO_AUTH=1`.** The flag loads the documented fixture `ADV-0001` from `session/fixtures/users.json` through the existing `JsonUserRepository(demo_roles=...)`; without it only customers exist. A password is always required — the flag admits a documented user, not a bypass. Alternative: hard-coded always-on advisor (rejected — the repo is public and an always-present second role invites testing it in production).

**4. `GET /api/v1/handoffs` and `/{id}` are role `advisor`, read-only.** The list plus `/{id}` returns the full package: summary, per-turn conversation, verified facts, actions attempted, evidence, open questions, plus customer id and country (the advisor's privilege, kept off the customer's routes). Customers get 403 + `access_denied`. The query reads the filed cases (`kind=handoff`) from the state store — tickets are rows, not a log scrape.

**5. One page, role landing decided in the browser from `/api/v1/auth/me`.** `app/static/app.js` fetches the role: customers land on the chat (which renders the handoff card from the typed `handoff` variant), advisors land on the ticket view fed by the handoffs API. Plain HTML/JS in `app/static/` per decision [006](../../../docs/build/decisions/006-frontend.md); no second page and no build step. Alternative: server-rendered per-role routes (rejected — adds templating to a process whose page is already static).

**6. An escalating turn with no named charge falls back to the last charge verified earlier in the session.** The handoff card must show a charge; when the customer's words escalate without a reference, the turn cycle reuses the most recent charge already verified in this conversation rather than filing an empty ticket.

**7. `sentinel-login/` keeps only `README.md` and its original page as a reference.** Backend, tests and packaging are deleted so there is exactly one app to run; the reference page stays because decision [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md) records it as provenance, not as a served app. The admin panel is not migrated — explicitly out of scope.

## Risks / Trade-offs

- [Demo flag left enabled outside the demo] → default off; with the flag off only customers exist; tests cover both states.
- [Advisor route exposes customer id] → only on `require_advisor` routes; customer routes still never return it; B11/B12 pin the 403s.
- [Path break hits every consumer at once] → routes, tests, page and eval runner move in one commit; `test_ui.py` covers the landing.
- [Fixture user becomes a real-looking account] → `ADV-0001` is documented as a mock in the fixtures and README; password still required.

## Migration Plan

One commit: dependencies and auth paths first, then the handoffs router, then the page and tests, then adversarial B11/B12 frozen in `evidence/adversarial/20261001T130342Z/`. A second commit removes the `sentinel-login/` backend. Rollback is reverting those commits; the flag means no config change is needed to disable the advisor.
