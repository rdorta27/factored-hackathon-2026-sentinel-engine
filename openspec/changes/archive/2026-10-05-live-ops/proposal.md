---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

`runtime-and-ci` redeployed the public link on 2026-10-03 (PRs #52, #53). Four gaps remain before the final redeploy:

- The deploy generates a random session salt when `.env` has none. This breaks `session_ref` continuity across redeploys.
- The workflow's list of replayable runs is almost empty.
- The checks of other plans have no script: the three demo cases, the phone layout, the login of the judges and the rule that the link has no passwordless entry. `post-freeze` and `judge-access` need one script that does all of them.
- Tests on the link leave sessions, disputes and tickets on the Azure Files share. A redeploy keeps the share.

It cites REQ-0027, REQ-0028, REQ-0035, REQ-0050 and REQ-0052.

## What Changes

- **Required salt:** the deploy stops when `SENTINEL_SESSION_SALT` is missing.
- **CI replay list:** the runs that verify offline today (`2024Q4-resolution-v1`, `2024Q4-resolution-v2`, `2024Q4-calibration-v1` and `2024Q4-train-v1`). `post-freeze` adds the later runs.
- **End-to-end check:** `scripts/e2e_check.py` with a base URL. It runs the three demo cases and the manual test replay, enters by persona or by password, reads the judge credentials from the ignored sheet, checks the phone layout at 390 px, and has an `--access-check` mode. One table with pass or fail and an exit code.
- **State reset:** `deploy/azure/reset-state.sh` removes the SQLite file and the turn log from the share.
- **Final redeploy:** moved to `post-freeze`.

## Capabilities

### New Capabilities
- `live-operations`: the stable salt, the replayed runs, the end-to-end check and the state reset.

### Modified Capabilities
(none)

## Impact

- `deploy/azure/deploy.sh`, `deploy/azure/reset-state.sh`, `deploy/azure/README.md`, `.github/workflows/tests.yml`, `scripts/e2e_check.py`, `scripts/capture_ui_product.py`.
- Not changed: application code and the record format.

## Non-goals

- More replicas, Postgres, alerts or dashboards; real Gold on the public link.
- The final redeploy and the runs on the link (`post-freeze`).
- Writing, printing or storing a plain password.
