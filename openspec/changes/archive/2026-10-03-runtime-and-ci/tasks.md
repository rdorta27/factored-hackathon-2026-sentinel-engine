# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md), [013](../../../docs/build/decisions/013-experiment-tracking.md). Paths are relative to the repository root.

## 1. Runtime code

- [x] 1.1 Standard-output sink behind `SENTINEL_LOG_STDOUT` and configurable `SENTINEL_SQLITE_JOURNAL`; fail fast on an unwritable state path. Evidence: tests in `sentinel-ai-core/tests/test_observability.py` (captured stdout, no customer id) and `tests/test_state_sqlite.py` (`DELETE` mode, read-only directory).

## 2. Workflow

- [x] 2.1 Add `.github/workflows/tests.yml` (two package jobs, no secrets, `SENTINEL_WRITE_EVIDENCE=0`, verify of replayable runs) and document the local commands in the README. Evidence: the file and a green run on the pull request. Green on [PR #52](https://github.com/rdorta27/factored-hackathon-2026-sentinel-engine/pull/52): `ai-core`, `data-engine` and `scan` succeeded. The data-engine job needed a current setuptools backend and `fetch_arrow_table()` (`247bb35`).

## 3. Deployment

- [x] 3.1 Extend `deploy/azure/deploy.sh` (storage account, share, mount, paths, journal mode, stdout logging, one replica), keep local defaults in the Dockerfile, document services, cost and retention in `deploy/azure/README.md`. Evidence: the script and a local `docker run` reaching `/api/v1/health`.
- [x] 3.2 After the redeploy, file a handoff and open a dispute, restart the revision and read both back; query the turn records in Log Analytics by country and outcome. Evidence: results and query text, without identifiers, under REQ-0035 in `docs/requirements/delivery.md`.
- [x] 3.3 Update README limitations (state, deployment), the path to production in `docs/architecture/specification.md`, REQ-0027 and REQ-0052 evidence. Evidence: those files.
