---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# One app, state outside the process

## Choice

The submission serves one FastAPI app (`app.main:app`) with one API under `/api/v1`: auth, transactions, chat, disputes, handoffs and health. Sessions, conversation state, disputes and handoff tickets are in SQLite, outside the process. The team integrated this on 10/1 (PR #23).

## Why

- **Two apps existed before.** The documented command started an app whose chat skipped the policy engine and had no login. The measured app was not served. One app removes this gap: we serve what we measure.
- **Mentor feedback: keep conversation state outside the process.** With state in memory, a restart lost every conversation. A second instance could not share it. SQLite keeps the state across a restart. Logout or expiry deletes it (REQ-0001, REQ-0027).
- **Ports keep the demo and production on the same code.** Gold (DuckDB view or labelled mock), state (SQLite or memory) and model (baseline or router) are adapters behind ports. Only the configuration changes.
- **A dispute is a preview, then a create,** on the same turn cycle as the chat. No write skips the confirmation (REQ-0004).

## Evidence

| Check | Where | Result |
|---|---|---|
| A dispute and a handoff ticket survive a restart of the live service | [REQ-0035](../requirements/delivery.md#req-0035), redeploy of 2026-10-03 with an Azure Files share | both still present after `az containerapp revision restart`; health 200 |
| The health route reports the state backend and answers 503 when the store fails | `GET /api/v1/health` | `state_backend: sqlite` on the live link |
| One open dispute per charge, same idempotency key | spec [`disputes`](../../openspec/specs/disputes/spec.md), [`dispute-confirmation`](../../openspec/specs/dispute-confirmation/spec.md) | tests pass in CI |

## Alternatives rejected

- **Keep both apps.** Two behaviors under one name. The evidence would describe an app that nobody runs.
- **PostgreSQL now.** More to operate for a single-instance demo. It is the production step, with the same models.

## In production

PostgreSQL on Azure behind the same models, more than one instance, and a queue to the bank CRM for handoffs ([015](../build/decisions/015-handoff-delivery.md)).

## On the slide

"One app, one API, and state that survives a restart. The demo and production differ only in the adapters behind the ports."
