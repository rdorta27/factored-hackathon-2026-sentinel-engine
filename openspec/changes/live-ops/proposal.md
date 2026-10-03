# Proposal

## Why

`runtime-and-ci` built the pieces for a durable public link (an Azure Files share for SQLite and the turn log, `DELETE` journal, one replica, turn records on standard output for Log Analytics) and a test workflow, but the live service still runs an image from before PRs #49 and #50: `GET /i18n/es-419` lacks `charge.not_found` and `extraction.refused`. Three gaps remain before the video. The deploy script generates a random session salt when `.env` has none, which breaks `session_ref` continuity across redeploys; nobody has yet shown that a handoff and a dispute survive a restart, or queried the records by country; and the workflow's list of replayable runs is empty (`runs=()`), so no frozen run is checked on each change (REQ-0025, REQ-0027, REQ-0028, REQ-0035, REQ-0050, REQ-0052).

## What Changes

- **Session salt is required:** the deploy stops when `SENTINEL_SESSION_SALT` is missing, instead of generating one.
- **One redeploy** with everything merged by then (at least PRs #49 to #51 and `ui-product` if merged), checked remotely: health, the new locale keys, and the three demo cases.
- **Restart check:** file a handoff and open a dispute, restart the revision, read both back.
- **Platform log queries:** saved Log Analytics queries over the turn records by country (MX, CO, AR), outcome (`ok`, `rejected`, `failed`, `timeout`) and language (`es-419`, `pt-BR`): turns, p50 and p95 latency, failures, handoffs, cost. Results recorded as aggregates only.
- **CI replays frozen runs:** the workflow lists every run that verifies offline (`2024Q4-resolution-v1`, and `2024Q4-eval-v7` if its fixed comparison now passes) and runs `python3 -m eval.run verify` for each.
- **Docs:** REQ-0035 evidence, `delivery.md`, README deployment line and the path to production.

## Capabilities

### New Capabilities
- `live-operations`: what the public service must prove after a redeploy, how it is monitored by country, and what the workflow replays.

### Modified Capabilities
(none)

## Impact

- `deploy/azure/deploy.sh`, `.github/workflows/tests.yml`, a queries file under `deploy/azure/`, `docs/requirements/delivery.md`, README, `docs/architecture/specification.md`.
- Not changed: application code, the record format.

## Non-goals

- More replicas, Postgres, alerts or dashboards.
- Real Gold on the public link.
- The re-measure after `chat-loop` (that is `evaluation-final`).

## Assumptions

- `runtime-and-ci` is merged before this starts.
- Done once, after `ui-product` and `evaluation-final` merge, so the video uses a single redeploy; a later `router-v3` serve needs another.
