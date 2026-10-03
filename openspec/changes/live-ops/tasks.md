# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md). Starts after `runtime-and-ci` merges. Paths are relative to the repository root.

## 1. Before the redeploy

- [ ] 1.1 Make `deploy/azure/deploy.sh` stop when `SENTINEL_SESSION_SALT` is missing; document it in `deploy/azure/README.md`. Evidence: the script and a dry run without the variable that exits early.
- [ ] 1.2 Fill the workflow's replay list with every run that verifies offline and run `eval.run verify` for each. Evidence: `.github/workflows/tests.yml` and a green run on the pull request.

## 2. Redeploy and prove it

- [ ] 2.1 Redeploy once from `main` after `ui-product` and `evaluation-final`; check health, the new locale keys and the three demo cases remotely. Evidence: results without identifiers under REQ-0035 in `docs/requirements/delivery.md`.
- [ ] 2.2 File a handoff and open a dispute, restart the revision, read both back. Evidence: the same section.
- [ ] 2.3 Save the KQL queries by country, outcome and language and record their aggregates after demo traffic. Evidence: `deploy/azure/queries.kql` and the aggregates under REQ-0035.

## 3. Close

- [ ] 3.1 Update README deployment and limitations, the path to production in `docs/architecture/specification.md`, and REQ-0035, REQ-0050 and REQ-0052 evidence. Evidence: those files.
