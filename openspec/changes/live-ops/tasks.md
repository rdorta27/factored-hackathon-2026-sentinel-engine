# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are relative to the repository root.

**Mode.** Every task is automatic. No task waits for the owner or for another plan, runs `az`, pushes or opens a pull request. The checks run against a local app. The final redeploy and the runs on the link are in `post-freeze`.

**Priority (the submission is due on 2026-10-05, 11:59 PM COT).** Required: 1.1, 1.3, 1.4, 1.5 and 1.7. The checks on the link need the credentials (1.5) because the one-click entry is off. Cut first if time runs out: 1.2, 1.6 and the tests of 1.8. Keep the note on the order of use in `deploy/azure/README.md`.

## 1. Now

- [ ] 1.1 Make `deploy/azure/deploy.sh` stop when `SENTINEL_SESSION_SALT` is missing and document it in `deploy/azure/README.md`. Evidence: the script and a dry run without the variable that exits before any `az containerapp` call.
- [ ] 1.2 Seed the workflow's replay list with `2024Q4-resolution-v1`, `2024Q4-resolution-v2` and `2024Q4-calibration-v1` (all three matched on 2026-10-04), and `2024Q4-train-v1`. The later runs (`2024Q4-eval-v8` and the robustness runs) do not exist yet: `post-freeze` adds them (tasks 2.4 and 3.3). Do not add `2024Q4-eval-v7`: its system block does not reproduce. Evidence: `.github/workflows/tests.yml` and a green run on the pull request.

- [ ] 1.3 Write `scripts/e2e_check.py`: one command, `--base-url`, that runs the three demo cases in es-419 and pt-BR and `scripts/manual_test_replay.py` (`docs-followups` renamed it from `felix_replay.py`; keep the script name in one constant), and prints one pass or fail table with a non-zero exit code on a failure. On a loopback URL it starts a local app with a clean SQLite file and the Gold mock, as `manual_test_replay.py` does. On a remote URL it uses the running service and starts nothing. If `GET /api/v1/auth/demo` answers 200, it enters by persona. If it answers 404 (the public link), it enters by password with the credentials of task 1.5. It reuses `scripts/sentinel_client.py`. Evidence: the script, a test of the pass and fail logic with a fake service, and a run against a local app.

- [ ] 1.4 Write `deploy/azure/reset-state.sh`: it removes the SQLite file and `turns.jsonl` from the Azure Files share, with the app scaled down or the replica restarted, and then checks that `/api/v1/health` answers. Document it in `deploy/azure/README.md`. A redeploy keeps the share, so tests on the link leave their sessions, disputes and tickets. Evidence: the script, the README and a dry run that prints the commands without running them. Ref: decision 019.

- [ ] 1.5 Make `scripts/e2e_check.py` read the judge logins and passwords for a remote base URL from the sheet that `scripts/make_judge_users.py` writes (`deploy/judge-users/passwords.csv`, columns login, role and password). Take its path from `SENTINEL_E2E_CREDENTIALS_FILE`. Never print or log a password. Without the variable, stop with a clear message before any request. From `judge-access` 2.4. Evidence: the script and a dry run without the variable.
- [ ] 1.6 Make the phone check in `scripts/e2e_check.py` a real pass or fail at 390 px: no horizontal scroll, the chat form visible, the build line and the judge guide present and closed. `scripts/capture_ui_product.py` starts its own app and enters by persona, so it cannot run against the link. Add a `--base-url` and a login by the credentials file to it, or write the check with the same Playwright setup. Evidence: the script and a run against a local app and against a local app with the one-click entry off (`SENTINEL_DEMO_PERSONAS=0`).
- [ ] 1.7 Add `--access-check` to `scripts/e2e_check.py`: the persona route answers 404; one login with the documented fixture password fails with HTTP 401 for each of the four logins; each judge credential logs in with the expected role and country. Make only one failed attempt for each login: the lockout lasts 15 minutes, and the judge logins are the same four names. Never print a password. For `post-freeze` task 4.6. Evidence: the script and a run against a local app started with the judge users file.
- [ ] 1.8 Test the three modes (cases, credentials, access check) with a fake service, and run the script once end to end against a local app. State in `deploy/azure/README.md` the order for the link: run `--access-check` first, then the cases, then `reset-state.sh`. A second run of the cases on a dirty state can fail, because the charge of the normal case is already in review. Evidence: the tests and the README.

## Moved to `post-freeze`

The deploy variables (old 2.0) and the final redeploy with its checks (2.1) now live in the `post-freeze` change. They need frozen code and the verdict of `eval-v8`. This plan closes when tasks 1.1 to 1.3 are merged.
