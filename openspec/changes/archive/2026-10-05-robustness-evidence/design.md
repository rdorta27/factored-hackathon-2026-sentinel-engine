---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Recorded answers for the load test.** The model is the slowest and the most expensive part. The main load run replays recorded answers, so it measures the service. A second, small run with the live model shows the real latency under load.
2. **Faults come from the ports.** The fault run swaps each adapter (model, Gold, case store) for one that times out, fails or returns invalid data. No code path exists only for tests.
3. **One case per candidate is a database fact.** The parallel test uses the SQLite store and the idempotency key. A unique constraint is the guarantee, not a lock in the process.
4. **The budget is per process and per day.** It reads the cost of each turn record. A restart keeps the running total in the state store.
5. **Every run is write-once** under `evidence/robustness/<run-id>/`, with `summary.json` and a `verify` where it is deterministic, and goes into `evidence/README.md`.

## Risks

- A load test on a laptop is not the cloud replica. Mitigation: state the machine and the CPU limit, and run once in a container with the same limits as Container Apps (0.5 vCPU, 1 GiB).

## Coordination (2026-10-04)

6. **The 429 `trace_id` is in `flow-fixes`.** This change does not touch the body of the rate-limit reply; its tests only read it.
7. **Reuse the HTTP helpers.** `flow-fixes` writes `scripts/felix_replay.py` with a small HTTP client for a running app. The load script and the fault runner reuse that client once `flow-fixes` is merged.
8. **Spend guard after `router-v3`.** Both change `app/ai/serving.py`. Merge `router-v3` first.
9. **Do not commit `uv.lock`.** Use the full interpreter path in `.local/final-push/02-sesiones.md` if `pytest` is not found.

10. **Merge after `chat-start`.** The five-minute expiry changes the confirm box in `app/orchestrator/`, which `chat-start` also changes. Rebase on `chat-start` before the merge.
