# Design

## Context

After PR #43, `gold_service.gold_duckdb_path()` returns `SENTINEL_GOLD_DUCKDB` if it exists, else the first existing of four paths relative to the working directory (`data/gold_bank.duckdb`, `sentinel-data-engine/data/…`, `../sentinel-data-engine/data/…`, `../data/…`), and `select_gold` probes it before the Delta folder and the mock. Each read opens the file read-only. Demo users come from `app/session/fixtures/users.json` (`CUST-0001` to `0003`), or from `SENTINEL_USERS_PATH`. `app/observability/records.py` rejects `CUST-\d+` and IPv4. The view has 4,425,008 rows, 1,352 with `days_since_transaction < 0`, and 57,329 MX, 34,529 CO and 22,748 AR customers with an approved charge in the last 90 days. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:** a real-data demo that starts the same way every time and logs in as real customers. **Non-Goals:** serving real data from Azure.

## Decisions

**1. Repository-relative default.** Replace the working-directory candidates with `SENTINEL_GOLD_DUCKDB` or `<repo>/sentinel-data-engine/data/gold_bank.duckdb`, resolved from the package location (as `var_dir()` does). Fewer paths, one behaviour.

**2. Filter in SQL.** Add `transaction_date <= reference date` to both queries; the reference date is passed by the store.

**3. Users script.** `scripts/` script: reads the file read-only, picks per country one customer with a recent approved charge below both thresholds, one above the high-amount threshold and one above the fraud score, hashes a password from the environment with `app/session/security.py`, writes JSON to a git-ignored path, prints counts. Ids never reach stdout.

**4. Guard regex.** Add `CLI-[A-Z0-9]{8,}` beside `CUST-\d+`.

**5. Tests on a temporary file.** A fixture builds a small DuckDB file with the view and invented rows (one future-dated, two customers) for selection, isolation, the future filter and the probe.

## Risks / Trade-offs

- **Real merchants and many rows per customer:** the three newest may not be the one meant; `chat-loop` narrowing helps; noted in the manual test.
- **Video shows ids:** mask them in anything shown.
- **The file is rewritten by a pipeline run while the app reads:** the per-call open fails safe; restart after a pipeline run.
