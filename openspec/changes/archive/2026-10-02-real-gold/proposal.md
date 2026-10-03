# Proposal

## Why

PR #43 made the app read the PII-free view from `gold_bank.duckdb`, but the real-data demo still does not work end to end. Checked on 2026-10-02 with the regenerated file: the demo users `CUST-0001` to `CUST-0003` have 0 charges in real Gold (real ids look like `CLI-…`), so a local run that picks the file shows an empty list; the file is found through paths relative to the launch folder, so the same command gives mock or real data depending on where it starts; 1,352 rows are dated after the reference date; the log guard that rejects customer ids only knows `CUST-\d+`; and no test reads a DuckDB file. The brief asks for a normal resolution path grounded in permitted records, with identity from a trusted test session (REQ-0003, REQ-0009, REQ-0015, REQ-0047).

## What Changes

- The Gold file is chosen explicitly: `SENTINEL_GOLD_DUCKDB` or one path relative to the repository, never the launch folder; the health route keeps reporting the source.
- Rows dated after the reference date are excluded in the query.
- A script writes a local users file for real customers (one or more per country with a recent approved charge, and one per handoff rule) outside git, printing counts only, for `SENTINEL_USERS_PATH`.
- The log guard rejects the real customer-id shape too.
- Tests read a temporary DuckDB file with the same view and invented rows.
- The normal, ambiguous and handoff cases run on real Gold in es-419 and pt-BR, recorded as outcomes without ids.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `gold-layer`: explicit file selection, future-dated rows, local users for real customers, evidence without rows.
- `observability`: the personal-data guard covers real customer ids.

## Impact

- `sentinel-ai-core/app/services/gold_service.py`, `app/tools/gold_duckdb.py`, `app/observability/records.py`, a script under `scripts/`, `.env.example`, tests.
- Docs: README limitations, `team/component-status.md`, tasks 3 and 4, REQ-0009 and REQ-0015 evidence, `team/chat-manual-tests.md`.
- Not changed: the pipeline, the public deployment (stays on the mock), the policy engine.

## Non-goals

- Real Gold on the public link: the file is 880 MB and rows may not be committed.
- Pipeline changes (Silver columns are Natalia's).
- Read time budget: in `chat-loop`.

## Assumptions

- The reference date 2026-06-17 equals the view's snapshot date.
- Supersedes the change `real-gold-read`.
