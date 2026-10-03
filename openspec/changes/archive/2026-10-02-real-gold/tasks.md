# Tasks

Areas: [data](../../../docs/build/areas/data.md). Decisions: [008](../../../docs/build/decisions/008-pii-gold-handling.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

## 1. Adapter

- [x] 1.1 Choose the file from `SENTINEL_GOLD_DUCKDB` or one repository-relative path; honour `mock`; keep the health source. Evidence: tests starting from two folders and with `mock` set, over a temporary DuckDB file.
- [x] 1.2 Exclude rows after the reference date in both queries. Evidence: a test with a future-dated row in the temporary file.
- [x] 1.3 Add the `CLI-` shape to the record guard. Evidence: `tests/test_observability.py` rejecting a record with a dataset-shaped id.
- [x] 1.4 Update `.env.example` and `sentinel-ai-core/README.md`. Evidence: those files.

## 2. Real users

- [x] 2.1 Write the users script (per country: eligible, high amount, fraud score), counts only, output git-ignored. Evidence: the script, a test over the temporary file that stdout has no ids, `git check-ignore` output in the commit body.

## 3. Run on real Gold

- [x] 3.1 Start with the real file and the users file; check `/api/v1/health` reports `duckdb`; run the normal, ambiguous and handoff cases in es-419 and pt-BR. Evidence: outcomes without ids in `team/chat-manual-tests.md`.
- [x] 3.2 Update README limitations, `team/component-status.md`, tasks 3 and 4 in `team/tasks.md`, REQ-0009 and REQ-0015 evidence: real Gold runs locally, the public link stays on the mock. Evidence: those files.
