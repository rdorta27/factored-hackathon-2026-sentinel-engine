# Design

## Context

See proposal.md for why. `sentinel-ai-core` already has `step()`, the policy engine, and session-bound tool ports. `step()` still takes the first looked-up charge. `sentinel-login/` has the test session, grounding, and the customer page, and its `POST /chat` opens a dispute on `selected_reference`. The submission process is `sentinel-ai-core` only.

## Goals / Non-Goals

**Goals:**

- One chat contract: `message` plus `selected_reference`, wired to `step()` and the engine.
- Grounding chooses a charge. Policy still decides.
- The customer page shows a confirm box before any write.

**Non-Goals:**

- Role landing, the advisor queue, and the admin panel are deferred, tracked in pending decision 29. This change does not specify or implement them.
- Do not build the full handoff package or persist a queue. `handoff` is a chat response.
- Do not change `evaluate()` order, country files, or `GoldTransactions` signatures.

## Decisions

### Wire field, two meanings

Keep the login body name `selected_reference`. Map it to the loop's structured candidate id. No pending box means selection, then policy. A pending box that matches means confirmation. A written yes stays text.

Alternative rejected: a second client field for confirmation. One field already exists, and the state distinguishes the turns.

### Token stays in the server

`step()` issues the token on the confirmation turn and passes it only to `open_dispute`. The HTTP body and the JSON response do not carry it.

Alternative rejected: echoing the token to the page. The page already sends the candidate id. A token in the browser can be replayed.

### Grounding is the Understand fake

Parse `es-419` and `pt-BR` in `app/ai/`, after person and out-of-scope checks. A match is input to policy. Do not call `open_dispute` from grounding. Do not take `candidates[0]`. Rank with the demo date, never the wall clock. Map a mock `Refunded` status to Reversed so the status rule applies. Do not treat "no reconozco" or "não reconheço" (unrecognized charge) as fraud.

Alternative rejected: leaving grounding in the login router. That router is not the decider.

### One demo clock

`app/session/` reads `SENTINEL_REFERENCE_DATE` once (default `2026-06-17`) and injects it as `Ports.today`. The engine does not read the environment. YAML `demo_today` remains the fallback when the variable is unset. The same value is the Gold as-of mark and the date on screen.

Alternative rejected: a second clock in the country file at runtime. Two clocks drift.

### Gold behind the existing port

Bind `customer_id` in an adapter before `step()`. `lookup_transactions()` gains no customer argument. `open_dispute` and `lookup_dispute` stay on the in-memory half. `GET /transactions` is a new session-scoped read over that adapter, not `/api/v1/transactions`. A customer identifier on that request is rejected.

Alternative rejected: passing `customer_id` into `step()`. Decision 005 forbids it.

### Session routes are not `/auth/*`

`POST /session/login`, `POST /session/logout`, and `GET /session/me`. Cookie is `HttpOnly`. Country on the session becomes `Ports.country`. Only the `customer` role is exercised.

### Page

Copy the customer subset into `app/static/`. Read `branding/` as-is. The confirm box uses `.chat-confirm`. A chip or a panel tap posts `selected_reference` and stops at the box. The agent control sends a person request, not an English sentence: first press offers help, second hands off. The opaque id may travel in JSON and must not be rendered.

### Decisions 004, 005, and 006

- 004: option 2 only. Tools return amount, currency, merchant, date, status, and an opaque id. Typed text still reaches the Understand fake. State that limitation. No token vault.
- 005: one FastAPI process, plain-Python loop. Idempotency key is `session_ref + candidate + action`. LangGraph stays deferred.
- 006: one page, same process, structured confirmation, no `customer_id` in the body.

### What stays on the old specs

`auth-login`, `roles`, `disputes`, `policy-engine`, and `decision-priority` are not deltas. They still describe `sentinel-login/` or the engine as already built. Do not archive them in this change.

## Risks / Trade-offs

- [Risk] Two apps both expose `POST /chat` if someone starts `sentinel-login`. → Mitigation: the ai-core README states it is the only submission server. Do not delete the old package.
- [Risk] Role landing, the advisor queue, and the admin panel are still open. → Mitigation: deferred, tracked in pending decision 29. Do not specify or implement them here.
- [Risk] A foreign `selected_reference` could leak a row if the adapter filters late. → Mitigation: resolve inside the session customer's rows before any fact is returned. Absence is not a write.
- [Risk] Incrementing clarification count on a successful match can trip `fields.missing` once mandatory fields are set. → Mitigation: increment only when the charge is still missing.

## Migration Plan

1. Land session, the Gold adapter, and `GET /transactions` with tests. The old package is untouched.
2. Teach the loop to select by grounding, then wire `POST /chat`.
3. Serve the page from ai-core. Confirm the old pytest and the new pytest run separately.
4. Rollback is not starting the new process. `sentinel-login/` remains runnable as a reference, not as the submission server.

## Open Questions

None. Route names, the two meanings of `selected_reference`, and leaving the old package in place are decided above.
