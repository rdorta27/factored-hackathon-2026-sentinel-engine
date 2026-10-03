# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are relative to the repository root.

## 1. Now

- [ ] 1.1 Make `deploy/azure/deploy.sh` stop when `SENTINEL_SESSION_SALT` is missing and document it in `deploy/azure/README.md`. Evidence: the script and a dry run without the variable that exits before any `az containerapp` call.
- [ ] 1.2 Seed the workflow's replay list with `2024Q4-resolution-v1`, add `2024Q4-eval-v7` only if `verify` passes, and run `eval.run verify` for each. Evidence: `.github/workflows/tests.yml` and a green run on the pull request.

## 2. After evaluation-final, ui-product and router-confidence merge

- [ ] 2.1 Redeploy once from `main`; check health, the new locale keys, the demo personas and the three demo cases remotely; save the KQL queries by country, outcome and language and record their aggregates; update REQ-0035, REQ-0050 evidence and the README deployment line. Evidence: results without identifiers under REQ-0035 in `docs/requirements/delivery.md` and `deploy/azure/queries.kql`.
