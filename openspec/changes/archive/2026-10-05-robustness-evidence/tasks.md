---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are under `sentinel-ai-core/` unless stated.

## 1. Code (merge early)

- [x] 1.1 Find blocking calls in async routes and fix them or measure them. Evidence: a test or a timing note in the commit body.
- [x] 1.2 Add the daily spend guard with the `budget` route. Evidence: `tests/test_model_serving.py`.
- [x] 1.3 Add the parallel-confirmation test. Evidence: `tests/test_confirmation.py` opens one case for N calls.
- [x] 1.4 Add the fault adapters and the fault-injection runner. Evidence: tests for each fault.
- [x] 1.7 Give `PendingConfirmation` a creation time and refuse a confirmation older than five minutes, so the loop asks again. Evidence: `tests/test_confirmation.py`.
- [x] 1.8 Add the strict Gold mode with a maximum age. Off by default. Evidence: a test that the app refuses to start when Gold is missing in strict mode, and starts with the mock when the mode is off.
- [x] 1.9 Chain the audit records: each record holds the hash of the previous one, and a check finds a changed or removed record. Evidence: `tests/test_audit_chain.py`.
- [x] 1.10 Add `bundle_hash` to `/health`: one hash of the policy files, the prompt examples and the cut-offs. Evidence: `tests/test_health.py`.
- [x] 1.11 In `sentinel-data-engine/tests`, add a test that an incremental load gives the same rows as a full load, row by row. Evidence: the test.
- [x] 1.5 Add the load-test script with recorded answers and a container limit option. Evidence: `scripts/load_chat.py` and a dry run.
- [x] 1.6 Remove unused dependencies from `pyproject.toml`. Evidence: a clean install and the full test suite.

## Moved to `post-freeze`

The fault-injection run (old 2.1), the load run (2.2) and the documents (3.1) now live in the `post-freeze` change. They need frozen code. This plan closes when the code and its tests are merged.
