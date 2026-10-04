---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are under `sentinel-ai-core/` unless stated.

## 1. Code (merge early)

- [ ] 1.1 Find blocking calls in async routes and fix them or measure them. Evidence: a test or a timing note in the commit body.
- [ ] 1.2 Add the daily spend guard with the `budget` route. Evidence: `tests/test_model_serving.py`.
- [ ] 1.3 Add the parallel-confirmation test. Evidence: `tests/test_confirmation.py` opens one case for N calls.
- [ ] 1.4 Add the fault adapters and the fault-injection runner. Evidence: tests for each fault.
- [ ] 1.5 Add the load-test script with recorded answers and a container limit option. Evidence: `scripts/load_chat.py` and a dry run.

## 2. Runs (after the code freeze)

- [ ] 2.1 Freeze the fault-injection run. Evidence: `evidence/robustness/<run-id>/summary.json`.
- [ ] 2.2 Freeze the load run (recorded answers, 0.5 vCPU, 1 GiB) and the small live run. Evidence: `evidence/robustness/<run-id>/summary.json`.

## 3. Documents

- [ ] 3.1 Write the four rationale pages, and update the sizing page, the metrics catalog, the evidence index and REQ-0021, REQ-0026 and REQ-0053. Evidence: those files.
