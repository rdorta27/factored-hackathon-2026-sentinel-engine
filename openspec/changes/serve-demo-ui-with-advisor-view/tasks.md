# Tasks

## 1. Backend

- [x] 1.1 `/api/v1/auth/*`, roles in code, demo advisor behind `SENTINEL_DEMO_AUTH` (evidence: `tests/test_handoffs_api.py`)
- [x] 1.2 `GET /api/v1/handoffs` and `/{id}` for role advisor (evidence: `tests/test_handoffs_api.py::test_advisor_reads_the_full_ticket`)
- [x] 1.3 Adversarial B11, B12 (evidence: `evidence/adversarial/20261001T130342Z/summary.json`)

## 2. UI and cleanup

- [x] 2.1 Role landing, advisor view, handoff card in `app/static/` (evidence: `tests/test_ui.py`)
- [x] 2.2 Remove the `sentinel-login/` backend, tests and packaging; README says reference UI only
