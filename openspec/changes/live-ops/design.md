# Design

## Context

After `runtime-and-ci`: `deploy/azure/deploy.sh` creates a 1 GiB Azure Files share, recreates the container app with one replica, mounts the share at `/mnt/sentinel`, sets `SENTINEL_VAR_DIR`, `SENTINEL_DB_PATH`, `SENTINEL_SQLITE_JOURNAL=DELETE` and `SENTINEL_LOG_STDOUT=1`; it reads `SENTINEL_SESSION_SALT` from `.env` and generates a random one if absent (lines 110 to 112 on `feat/runtime-and-ci`). `.github/workflows/tests.yml` runs both suites with `SENTINEL_WRITE_EVIDENCE=0` and has an empty `runs=()`. Turn records carry `trace_id`, `session_ref`, `step`, `tool`, `outcome`, `policy_rule`, `latency_ms`, tokens, `cost_usd`, `language`, `country` and `policy_version`. The live link runs an image without PRs #49 and #50. See proposal.md for motivation.

## Decisions

1. **Fail on a missing salt** rather than generate: a generated salt is lost with the container and breaks correlation.
2. **One redeploy for the video**, after `ui-product` and `evaluation-final`, checked by a short script that fetches health and the locale file and runs the three demo cases.
3. **Restart by revision restart**, not by recreating the app, so the share and the database stay.
4. **Queries in KQL** kept in `deploy/azure/queries.kql`, parsing the JSON line from the container's console log; results pasted as aggregates under REQ-0035.
5. **Replay list in the workflow**, starting with `2024Q4-resolution-v1`; `2024Q4-eval-v7` is added only if `verify` passes after the comparison fix of `resolution-eval`.

## Risks / Trade-offs

- **Log ingestion delay** of a few minutes: queries run after a wait.
- **Recreate deletes in-flight sessions:** the deploy happens before recording, not during.
- **SQLite on a share** stays a demo choice with one replica, stated in the README.
