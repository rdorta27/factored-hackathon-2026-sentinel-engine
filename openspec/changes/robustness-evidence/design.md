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
