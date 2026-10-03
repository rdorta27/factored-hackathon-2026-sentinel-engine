# Design

## Context

`Recorder` (`app/observability/writer.py`) writes to memory and `var_dir()/turns.jsonl` only. `app/db/session.py` sets `PRAGMA journal_mode=WAL`. The image sets `SENTINEL_VAR_DIR` and `SENTINEL_DB_PATH` under `/tmp/sentinel`, runs non-root, and `deploy/azure/deploy.sh` deploys one Container App. Container Apps forwards standard output to Log Analytics. Both packages declare a `dev` extra with pytest; the AI suite forces mock Gold in `conftest.py`; attacks without defence are strict expected failures. See proposal.md for motivation.

## Decisions

1. **Standard output as a third sink** behind `SENTINEL_LOG_STDOUT=1`; a bare logger prints `record.to_json()`. OpenTelemetry stays the production path.
2. **Azure Files share** created and mounted by `deploy.sh`; `SENTINEL_VAR_DIR` and `SENTINEL_DB_PATH` point at it. Postgres stays the production path.
3. **`SENTINEL_SQLITE_JOURNAL`** (default `WAL`, deployment `DELETE`); one replica pinned; startup fails fast if the path is not writable.
4. **Workflow:** one job per package (`pip install -e ".[dev]"`, `pytest -q`), `contents: read`, `SENTINEL_WRITE_EVIDENCE=0`, Python 3.12 with pip cache; a third step runs `python3 -m eval.run verify` for each run in a short list kept in the workflow.

## Risks / Trade-offs

- **SQLite on SMB** has weaker locking: one replica, `DELETE` journal, short transactions; declared as demo, not production.
- **Mount permissions** for the non-root user: mount options plus the startup check.
- **Hidden local state** making a test pass only locally: the first clean-runner run is the check.
- **Cost:** a small share and log ingestion inside the trial credit, stated in the deploy README.
