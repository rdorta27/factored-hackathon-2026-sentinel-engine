# Proposal

## Why

The public link keeps its turn log and SQLite state under `/tmp/sentinel` in the container (`deploy/azure/Dockerfile`). The log goes only to that file, so Azure never collects it: the deployed service has no tracing or monitoring, and a restart or scale-to-zero deletes sessions, disputes and handoff tickets, so an evaluator can file a handoff and find it gone. Separately, only `gitleaks` runs on a push or pull request, so a merge can break the app, the pipeline or an attack defence unnoticed. On 2026-10-02 both suites pass offline without keys or data: 522 tests plus 3 expected failures in `sentinel-ai-core`, 32 in `sentinel-data-engine`. The kickoff asks for tracing, monitoring, data retention, versioning and repeatable evaluation (REQ-0025, REQ-0027, REQ-0028, REQ-0035, REQ-0052).

## What Changes

- Turn records also go to standard output as JSON lines when enabled, so Container Apps sends them to Log Analytics.
- The deployment mounts an Azure Files share for SQLite and the log; SQLite's journal mode becomes configurable (`DELETE` on the share, since WAL needs shared memory a share lacks); one replica.
- A restart check shows a session, a dispute and a handoff ticket survive.
- A GitHub Actions workflow runs both suites on every push and pull request, with no secrets and no evidence writes, plus `eval.run verify` for the frozen runs that replay offline.

## Capabilities

### New Capabilities
- `deployment-runtime`: where the deployed service writes records and state, and what survives a restart.
- `continuous-checks`: what runs on every change and what it never does.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/observability/writer.py`, `app/db/session.py`, `deploy/azure/Dockerfile`, `deploy/azure/deploy.sh`, `deploy/azure/README.md`, `.github/workflows/tests.yml`, README.
- Not changed: record format, case store schema, app behaviour, tests.

## Non-goals

- Postgres or more than one replica (production path).
- Dashboards, alerts, deploy from CI, live-model or real-data checks in CI.

## Assumptions

- The verify step lists only runs that replay offline once `resolution-eval` is merged (its fix makes `eval-v7` comparable); a run that does not replay stays out.
- Supersedes the changes `durable-runtime` and `ci-tests`.
