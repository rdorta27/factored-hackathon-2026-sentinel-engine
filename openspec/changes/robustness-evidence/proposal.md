---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The brief asks for capacity limits, bounded retries, safe fallback and tool-failure handling with counts (REQ-0021, REQ-0026, REQ-0053). The review of 2026-10-04 found these gaps:

- Nobody measured the capacity of `/api/v1/chat`. `docs/sizing_capacity.md` measures DuckDB queries only.
- No run measures tool-failure handling as a rate. `docs/build/metrics.md` cites the adversarial categories only.
- No evidence shows that two parallel confirmations open one case.
- The public link has no daily model spend limit. Only the evaluation has a cap.
- Diego (MLE at Factored) warned that CPU-bound work can block the FastAPI event loop. Nobody checked it.

## What Changes

- **Load test:** a script drives `/api/v1/chat` with recorded model answers at increasing rates on one process. It records requests per second, p50 and p95, errors and 429 replies. A second run uses the live model with a small cap.
- **Fault-injection run:** model timeout, model 5xx, invalid JSON, slow Gold, Gold error, case-store error. For each fault: the outcome, the added latency and the share of turns with a safe reply.
- **Parallel confirmations:** N parallel confirmations of one candidate open exactly one case.
- **Event-loop check:** find synchronous work in async routes (DuckDB, SQLite, model calls). Move it to a thread pool, or prove it does not block, with a measurement.
- **Spend guard:** a daily model budget (`SENTINEL_LLM_DAILY_BUDGET_USD`). Above it, the keyword baseline answers, and the turn log marks `budget` as the route.
- **Documents:** four rationale pages (`failure-handling`, `capacity-and-latency`, `cost-guard`, `attack-coverage`), the sizing page and the metrics catalog.

## Capabilities

### New Capabilities
- `capacity-evidence`: the load test and its frozen run.

### Modified Capabilities
- `failure-tests`: the fault-injection run, parallel confirmations and the spend guard.

## Impact

- `sentinel-ai-core/app/ai/serving.py` (budget), routers with blocking calls, `eval/` or `scripts/` (load and fault runs), tests, `evidence/robustness/`, `docs/rationale/`, `docs/sizing_capacity.md`, `docs/build/metrics.md`.
- The measured runs use the final code. The code changes merge early; the runs freeze after the code freeze.

## Non-goals

- Autoscaling or PostgreSQL.
- A load test of the public link. One replica serves the demo, and the test must not cost the evaluators.
