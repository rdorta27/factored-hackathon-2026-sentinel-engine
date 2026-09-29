# Sentinel Login (test skeleton)

Mock backend for the Sentinel Engine banking assistant demo. Python 3.12,
FastAPI, Pydantic v2. No new runtime dependencies.

## Run

From this directory with the repo `.venv` (Python 3.12):

```
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Open `http://127.0.0.1:8000/` for the UI or `/docs` for the API.
Run tests with `..\.venv\Scripts\python.exe -m pytest -q`.

## Demo credentials (false, test-only)

| User | Password | Role | Lands on |
|---|---|---|---|
| `CUST-0001` | `Testpass-001` | customer | chat |
| `ADV-0001` | `Advisor-001` | advisor | escalated-case queue |
| `ADM-0001` | `Admin-001` | admin | audit and metrics |

These are invented demo values, not real secrets. Only `customer_id`
identifiers are invented too; no hackathon dataset rows are in this repo.

## Demo chat scenarios (mock orchestrator: intent only, facts from mock Gold)

| Message | Result |
|---|---|
| `I dispute the charge of 1000 at ACME` | verified Proof-of-Work receipt (`TXN-1001`) |
| `dispute the old charge from january` | handoff, 90-day refusal (`TXN-1002`) |
| `dispute the refunded charge` | handoff, refund refusal (`TXN-1003`) |
| `help with charge` | clarification asking for the transaction |
| `my card was stolen, fraud!` | handoff, visible in the advisor queue |
| `broken dispute flow error test` | retry then handoff, never a confirmation |
| `I want a human agent` twice | single offer, then handoff |
| Agent button | immediate handoff |

## Disputes API (deterministic policy gate)

`POST /api/v1/disputes/create` with `{"transaction_ref": "TXN-1001"}` and an
`Idempotency-Key` header: 201 plus the five Proof-of-Work elements for
eligible rows, 422 with reason plus handoff data otherwise.
`GET /api/v1/disputes/{case_id}/receipt` downloads the plain-text receipt.
Eligibility (90-day window per decision 003, not refunded, no prior dispute)
runs in code against mock Gold rows (`TXN-1001` eligible, `TXN-1002` stale,
`TXN-1003` refunded, `TXN-1004` disputed); DuckDB/Delta arrive in Phase 2.

## Limits (Phase 1)

Mocks everywhere (orchestrator, cases, queue); in-memory state lost on
restart; single process (`workers=1`); no model calls; no money movement.
