# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are relative to the repository root.

## 1. Now

- [ ] 1.1 Make `deploy/azure/deploy.sh` stop when `SENTINEL_SESSION_SALT` is missing and document it in `deploy/azure/README.md`. Evidence: the script and a dry run without the variable that exits before any `az containerapp` call.
- [ ] 1.2 Seed the workflow's replay list with `2024Q4-resolution-v1`, `2024Q4-resolution-v2` and `2024Q4-calibration-v1` (all three matched on 2026-10-04), and add each later run that verifies offline: `2024Q4-train-v1`, the robustness runs and `2024Q4-eval-v8`. Do not add `2024Q4-eval-v7`: its system block does not reproduce. Evidence: `.github/workflows/tests.yml` and a green run on the pull request.

- [ ] 1.3 Write `scripts/e2e_check.py`: one command that runs the three demo cases in es-419 and pt-BR, `scripts/felix_replay.py` and the phone screenshots against a base URL, and prints one pass or fail table. It reuses `scripts/sentinel_client.py`. Evidence: the script and a run against a local app.

## Moved to `post-freeze`

The deploy variables (old 2.0) and the final redeploy with its checks (2.1) now live in the `post-freeze` change. They need frozen code and the verdict of `eval-v8`. This plan closes when tasks 1.1 to 1.3 are merged.
