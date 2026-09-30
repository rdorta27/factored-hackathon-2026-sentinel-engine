# Sentinel Login (test skeleton)

Mock backend for the Sentinel Engine banking assistant demo. Python 3.12,
FastAPI, Pydantic v2. No new runtime dependencies.

## Run

From this directory with the repo `.venv` (Python 3.12):

```
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Open `http://127.0.0.1:8000/ui/` for the UI or `/docs` for the API.
Run tests with `..\.venv\Scripts\python.exe -m pytest -q`.

## Reference date (why it is not the real clock)

The dispute window needs a "today". This demo dataset is static and its last
date is **2026-06-17**, so using the real clock would put every charge months
outside the 90-day window and **nothing would ever be eligible**. The system
therefore reads its reference date from an environment variable:

```
..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# another window, for a different demo date:
$env:SENTINEL_REFERENCE_DATE="2026-06-17"; ..\.venv\Scripts\python.exe -m uvicorn app.main:app
```

Default: `2026-06-17`. The effective value is shown in the UI and in the
receipt, so a reviewer can always tell which "today" the rules used.

## Demo credentials (false, test-only)

| User | Password | Role | Country | Lands on |
|---|---|---|---|---|
| `CUST-0001` | `Testpass-001` | customer | MX (MXN) | chat |
| `CUST-0002` | `Testpass-001` | customer | CO (COP) | chat |
| `CUST-0003` | `Testpass-001` | customer | AR (ARS) | chat |
| `ADV-0001` | `Advisor-001` | advisor | — | escalated-case queue |
| `ADM-0001` | `Admin-001` | admin | — | audit and metrics |

These are invented demo values, not real secrets. Only `customer_id`
identifiers are invented too; no hackathon dataset rows are in this repo.
Each customer's currency comes from the account, never from the language.

## Demo chat scenarios (mock orchestrator: intent only, facts from mock Gold)

The mock returns what the customer said plus a Gold reference; grounding then
decides whether a case may open. A message whose date, amount, or merchant does
not match a transaction exactly gets a clarification with the candidates.

| Message | Result |
|---|---|
| `I dispute the charge of 1000.00 at ACME Store on 2026-06-10` | verified Proof-of-Work receipt (`TXN-1001`) |
| `I dispute the charge of 1000.00 at ACME Store on 2026-09-20` | clarification with candidates (wrong date) |
| `I dispute the charge of 1000.00 at ACME Store` | clarification (two charges match) |
| `I dispute the charge of 500.00 at ACME Store on 2026-06-05` | handoff, refund refusal |
| `I dispute the charge of 2500.00 at ACME Store on 2026-01-15` | handoff, 90-day refusal |
| `quero disputar a cobrança de R$ 1.000,00 na Loja ACME do dia 10 de junho` | Portuguese grounding |
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
