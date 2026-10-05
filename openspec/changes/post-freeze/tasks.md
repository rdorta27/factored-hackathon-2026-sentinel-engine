# Tasks

Order: gate, measure, runs, redeploy, close. A step reads the frozen output of the step before it. Each task names the plan it came from.

**Mode.** Task 1.1 asks the owner for four inputs. Every task after 1.1 is automatic: it needs no other answer, and it does not wait for another plan. A task never runs `git push`, opens a pull request or creates a tag.

**Priority (the submission is due on 2026-10-05, 11:59 PM COT).** Required: 1.1, 1.2, 4.1, 4.2, 4.3, 4.6, 4.4, 4.5 and 5.1. These redeploy the public link with the prompt that the verdict of `eval-v8-measure` chose, and check it. Do them in this order, because the video is recorded on the redeployed link. Cut first if time runs out, from the bottom: 6.1, 5.3, 5.2, 3.1 to 3.5 and 2.5.

## 1. Gate (G3)

- [x] 1.1 Check that the code is frozen and collect the four inputs of the owner. First check that these plans are merged: `flow-fixes`, `router-v3`, `chat-start`, `bank-ui`, `trained-baseline`, `charge-ranker`, `robustness-evidence` (code), `eval-v8` (rules, seal, rehearsal), `eval-v8-measure` (the measurement and its verdict), `evidence-hardening`, `demo-clarity`, `judge-access`, `live-ops` and `release` (the freeze procedure of `release` 3.2 exists). `pitch-site` and `docs-followups-2` are documents and do not block the gate. Then ask the owner for: (a) the confirmation that the code is frozen; (b) the total spend allowed for live model calls in tasks 2.5 and 3.4; (c) the OK to run `az` and redeploy the public link in section 4, and the Azure subscription to use; (d) the path of the judge sheet, to set `SENTINEL_E2E_CREDENTIALS_FILE`, and the path of the judge users file. Record the freeze commit, the `bundle_hash` of `/health` and the four answers (never a password) in `docs/build/delivery.md`. From `eval-v8` 4.1. Evidence: `git log` and the record. Ref: decision 018, ml area.
- [x] 1.2 Run `python3 scripts/e2e_check.py --base-url http://127.0.0.1:8000` against the local service (it starts a clean local app when the URL is loopback). Evidence: the pass table in the commit body. Ref: decision 019.

## 2. Live evidence (after the gate)

The measurement of `eval-v8`, its verdict, its reports and the error analysis moved to the `eval-v8-measure` change (old tasks 2.1, 2.2, 2.3, 2.4 and 2.6). That change runs before this one. This plan reads its verdict.

- [x] 2.5 Within the spend of input (b). Run the live timing mode of the resolution runner once on the frozen build, with the spend cap. Freeze it as `evidence/evaluation-runs/2024Q4-resolution-live-v1/` and add it to `evidence/README.md` (Simulation, live model call, mock store). Report p50 and p95 per call and per conversation, and cost per attempted case and per resolution. From `evidence-hardening` 2.4. Evidence: the run folder and the `/health` `bundle_hash`. Ref: REQ-0055.

## 3. Robustness runs (after the gate)

- [x] 3.1 Freeze the fault-injection run. From `robustness-evidence` 2.1. Evidence: `evidence/robustness/<run-id>/summary.json`. Ref: decision 019.
- [ ] 3.2 Freeze the load run (recorded answers, 0.5 vCPU, 1 GiB) and the small live run. From `robustness-evidence` 2.2. Evidence: `evidence/robustness/<run-id>/summary.json`. Ref: decision 019.
- [ ] 3.3 Write the four rationale pages (`failure-handling`, `capacity-and-latency`, `cost-guard`, `attack-coverage`). Update the sizing page, the metrics catalog, the evidence index, REQ-0021, REQ-0026 and REQ-0053. From `robustness-evidence` 3.1. Add each robustness run that verifies offline to the CI replay list of `.github/workflows/tests.yml` (from `live-ops` 1.2). Evidence: those files. Ref: ml area.
- [x] 3.4 Within the spend of input (b). Run the 3 attack cases that pass on the stand-in model against the real router model. Write a new adversarial run with `SENTINEL_WRITE_EVIDENCE=1` from `sentinel-ai-core/` and add it to `evidence/README.md`. From `evidence-hardening` 4.2. Evidence: `evidence/adversarial/<run-id>/summary.json`. Ref: REQ-0021.
- [ ] 3.5 Add the known limitation of the attack suite (category B), the three cases, the two model outputs without confidence in `calibration-v3` (one empty, one cut JSON; the per-turn baseline fallback covers them) and the two-decimal rounding of `t_act` to the limits page and to the README `## Limitations`. Update `docs/architecture/mocks.md`: the three cases now run on the real model. From `evidence-hardening` 4.3 and 5.3. Evidence: the page, the README and the new adversarial run. Ref: REQ-0013, REQ-0021.

## 4. Redeploy (after sections 2 and 3)

- [x] 4.1 Add `SENTINEL_BRAND_NAME`, `SENTINEL_BRAND_ACCENT`, `SENTINEL_LLM_DAILY_BUDGET_USD`, `SENTINEL_LLM_PROMPT_VERSION` (v3 only if the verdict of `eval-v8-measure` task 2.4 says so) and `SENTINEL_CHARGE_RANKER` (off) to `deploy/azure/deploy.sh`. Keep `SENTINEL_LLM_CUTOFFS` unset: the v3 cut-offs make the router ask for clarification in about 80% of turns (`evidence-hardening` 4.4) and its README. From `live-ops` 2.0. Evidence: the script and a dry run. Ref: decision 019.
- [x] 4.2 Authorized by input (c) of task 1.1. Run `deploy/azure/upload-users.sh` with the judge users file of input (d) (from `judge-access` 2.3), then redeploy once from `main`. Check health, the `bundle_hash` against task 1.1, the model and prompt served, the new locale keys, the demo personas, the three demo cases in es-419 and pt-BR, `scripts/manual_test_replay.py --base-url <link>` (`docs-followups` 7.1 renames `scripts/felix_replay.py`) and the phone layout. Save the KQL queries and record their aggregates. Update REQ-0035, REQ-0050 and the README deployment line. From `live-ops` 2.1. Evidence: the check output and `deploy/azure/queries.kql`. Ref: decision 019.
- [x] 4.3 Run `scripts/e2e_check.py --base-url <link>` against the link, with `SENTINEL_E2E_CREDENTIALS_FILE` set to the judge sheet. Run it after the access check of task 4.6 and before the reset of task 4.4. Use only the judge logins, one run, and no load. Evidence: the pass table. Ref: decision 019.
- [x] 4.6 Run `scripts/e2e_check.py --access-check --base-url <link>` (from `live-ops` 1.7 and `judge-access` 4.2) before task 4.3: the persona route answers 404, a documented fixture password fails and each judge credential works with the right role. Pass the credentials by environment variables. Evidence: the output in `docs/build/delivery.md`. Ref: REQ-0027.
- [x] 4.4 Reset the state of the link with `deploy/azure/reset-state.sh` (`live-ops` 1.4). A redeploy keeps the Azure Files share, so the tests of tasks 4.2 and 4.3 leave sessions, disputes and tickets. Evidence: a note of the command and the empty counts. Ref: decision 019.
- [x] 4.5 Check `GET /api/v1/health` once after the reset: the `bundle_hash` of task 1.1, the model, the prompt version and `gold_source`. Do not log in or send a chat turn after this check, because that writes state again. Evidence: the health output in `docs/build/delivery.md`. Ref: decision 019.

## 5. Close (after section 4)

- [x] 5.1 Regenerate `site/numbers.json` and update the slides with the frozen numbers. The diagrams of `pitch-site` 4.4 and 4.5 and the section 5.6 read the same file, so they update with it. Then run `python3 scripts/localize.py` and `python3 scripts/localize.py --check`, so the `es-419` and `pt-BR` copies and the three slide PDFs follow. From `pitch-site` 4.1. Evidence: the numbers test passes. Ref: REQ-0030.
- [x] 5.2 Review the README (links, numbers with their fields, limits). Add the last pull requests to the changelog. Check each row of the submission checklist. From `release` 4.1. Evidence: the diff and the checklist. Ref: decision 019.
- [x] 5.3 Write the release notes for `v0.9-demo` and `v1.0-submission` with the final numbers, and give the owner the exact `git tag v0.9-demo`, `git tag v1.0-submission` and `gh release create` commands, after the redeploy. From `release` 2.1. Evidence: the notes and the commands in `docs/build/delivery.md`. The owner runs them.

## 6. Hand over the closing documents (after section 5)

The closing documents moved to the `docs-followups-2` change. It runs after `release`. Nothing here changes code or the `bundle_hash`.

- [x] 6.1 Give the owner the record for `docs-followups-2`: the freeze commit, the `bundle_hash`, the model and prompt version served, the run ids of the final measurement, the robustness runs and the live latency run, and the date of the final redeploy. Evidence: the record in `docs/build/delivery.md`. Ref: decision 019.
