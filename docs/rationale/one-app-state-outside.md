# One app, state outside the process

## Choice

The submission serves one FastAPI app (`app.main:app`) with one API under `/api/v1` (auth, transactions, chat, disputes, handoffs, health). Sessions, conversation state and cases live in SQLite, outside the process. Integrated on 10/1 (PR #23).

## Why

- **Before, two apps coexisted:** the documented command started a track whose chat skipped the policy engine and had no login, while the measured app was not served. Specs and docs contradicted each other. One app removes that gap: what we measure is what we serve.
- **Mentor feedback: externalize conversation state.** With state in memory, a restart lost every conversation and a second instance could not share it. SQLite keeps it across restarts and deletes it on logout or expiry (REQ-0001, REQ-0027).
- **Ports keep the demo and production on the same code.** Gold (DuckDB view or labeled mock), state (SQLite or memory) and model (baseline or prompted router) are adapters behind ports; only configuration changes.
- **Disputes are preview then create,** on the same turn cycle as the chat, so no write skips the confirmation (REQ-0004).

## Alternatives rejected

- **Keep both apps:** two behaviors under one name; evidence would describe an app nobody runs.
- **Postgres now:** more to operate for a single-instance demo; it is the production step with the same models.

## In production

Postgres on Azure behind the same models, more than one instance, and a queue to the bank's CRM for handoffs ([015](../build/decisions/015-handoff-delivery.md)).

## On the slide

"One app, one API, and state that survives a restart; the demo and production differ only in the adapters behind the ports."
