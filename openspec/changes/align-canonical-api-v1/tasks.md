# Tasks

## 1. Contract and app

- [x] 1.1 Typed reply contract in `app/schemas/chat.py` (evidence: `tests/test_contract.py`)
- [x] 1.2 Chat, transactions and session routers under `/api/v1` (evidence: `tests/test_contract.py::test_old_paths_are_gone`)
- [x] 1.3 Single served app, `/api/v1/health` with Gold source (evidence: `tests/test_contract.py::test_served_app_is_the_full_app`)
- [x] 1.4 Remove production routers and `auth_compat.py`; keep `db/`, `models/` unmounted

## 2. Adapters and log

- [x] 2.1 DuckDB Gold adapter with fallback (evidence: `tests/test_gold_duckdb.py`)
- [x] 2.2 Handoff package on the closing turn record (evidence: `tests/test_contract.py::test_handoff_package_is_logged_on_the_turn_record`)

## 3. Consumers and evidence

- [x] 3.1 `app.js` paths, i18n keys in `es-419` and `pt-BR`
- [x] 3.2 Tests, adversarial suite and `eval/runner.py` on `/api/v1`
- [x] 3.3 New runs: `evidence/evaluation-runs/2024Q4-eval-v3/summary.json`, `evidence/adversarial/20261001T114008Z/summary.json`
