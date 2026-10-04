# Proposal

## Why

`runtime-and-ci` redeployed the public link on 2026-10-03 with an Azure Files share, one replica and turn records on standard output, showed that a dispute and a handoff survive a revision restart, counted the records by country in Log Analytics, and made the test workflow green (PRs #52, #53). Three gaps remain. The deploy still generates a random session salt when `.env` has none (`deploy/azure/deploy.sh`), which breaks `session_ref` continuity across redeploys. The workflow's list of replayable runs is empty (`runs=()`), so no frozen run is checked on each change. And the work merged after that redeploy (PRs #55 to #57, then `flow-fixes`, `chat-start`, `bank-ui`, `trained-baseline`, `robustness-evidence` and `router-v3`) needs one final redeploy before the video, checked and queried by country, outcome and language (REQ-0027, REQ-0028, REQ-0035, REQ-0050, REQ-0052).

## What Changes

- **Session salt is required:** the deploy stops when `SENTINEL_SESSION_SALT` is missing instead of generating one.
- **CI replays frozen runs:** every run that verifies offline is listed (`2024Q4-resolution-v1`, `2024Q4-resolution-v2` and `2024Q4-calibration-v1` now; later runs when they verify; not `2024Q4-eval-v7`, whose system block does not reproduce) and checked with `python3 -m eval.run verify`.
- **Final redeploy for the video:** one redeploy from `main` after the work above merges, checked remotely (health, the new locale keys, the demo personas and the three demo cases), with saved KQL queries by country, outcome and language and their aggregates recorded without identifiers.

## Capabilities

### New Capabilities
- `live-operations`: the stable salt, the replayed runs and the post-redeploy proof.

### Modified Capabilities
(none)

## Impact

- `deploy/azure/deploy.sh`, `deploy/azure/README.md`, `deploy/azure/queries.kql`, `.github/workflows/tests.yml`, REQ-0035 and REQ-0050 evidence, README deployment line.
- Not changed: application code, the record format.

## Non-goals

- More replicas, Postgres, alerts or dashboards; real Gold on the public link.
- The redeploy for a v3 router, which belongs to `router-v3`.

## Assumptions

- The salt and the CI list can land now; the final redeploy waits for `evaluation-final`, `ui-product` and `router-confidence`.
