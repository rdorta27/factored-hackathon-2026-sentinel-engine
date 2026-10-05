# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are relative to the repository root.

## 1. Now

- [ ] 1.1 Make `deploy/azure/deploy.sh` stop when `SENTINEL_SESSION_SALT` is missing and document it in `deploy/azure/README.md`. Evidence: the script and a dry run without the variable that exits before any `az containerapp` call.
- [ ] 1.2 Seed the workflow's replay list with `2024Q4-resolution-v1`, `2024Q4-resolution-v2` and `2024Q4-calibration-v1` (all three matched on 2026-10-04), and add each later run that verifies offline: `2024Q4-train-v1`, the robustness runs and `2024Q4-eval-v8`. Do not add `2024Q4-eval-v7`: its system block does not reproduce. Evidence: `.github/workflows/tests.yml` and a green run on the pull request.

- [ ] 1.3 Write `scripts/e2e_check.py`: one command that runs the three demo cases in es-419 and pt-BR, `scripts/felix_replay.py` and the phone screenshots against a base URL, and prints one pass or fail table. It reuses `scripts/sentinel_client.py`. Evidence: the script and a run against a local app.

## 2. After the code freeze

The code freeze is the merge of `flow-fixes`, `chat-start`, `bank-ui`, `trained-baseline`, the code of `robustness-evidence` and the served configuration of `router-v3`. `evaluation-final`, `ui-product` and `router-confidence` are already in `main`.

- [ ] 2.0 Add `SENTINEL_BRAND_NAME`, `SENTINEL_BRAND_ACCENT`, `SENTINEL_LLM_DAILY_BUDGET_USD` and `SENTINEL_LLM_PROMPT_VERSION` (v3 only if it passes `eval-v8`), `SENTINEL_CHARGE_RANKER` (as decided before the freeze) to `deploy/azure/deploy.sh` and its README. Evidence: the script and a dry run.

- [ ] 2.1 Redeploy once from `main`; check health, the new locale keys, the demo personas, the three demo cases in es-419 and pt-BR, the manual test of Felix (`scripts/felix_replay.py --base-url <link>`) and the phone layout remotely; save the KQL queries by country, outcome and language and record their aggregates; update REQ-0035, REQ-0050 evidence and the README deployment line. Run the end-to-end check (`scripts/e2e_check.py --base-url <link>`) before the video. Evidence: results without identifiers under REQ-0035 in `docs/requirements/delivery.md` and `deploy/azure/queries.kql`.
