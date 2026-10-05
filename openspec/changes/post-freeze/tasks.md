# Tasks

Order: gate, measure, runs, redeploy, close. A step reads the frozen output of the step before it. Each task names the plan it came from.

## 1. Gate (G3)

- [ ] 1.1 Confirm with the owner that the code is frozen: `flow-fixes`, `router-v3`, `chat-start`, `bank-ui`, `trained-baseline`, `charge-ranker`, `robustness-evidence` (code), `eval-v8` (rules, seal, rehearsal) and `live-ops` 1.1 to 1.3 are merged. Record the freeze commit and the `bundle_hash` of `/health`. From `eval-v8` 4.1. Evidence: `git log` and the record in `docs/build/delivery.md` (freeze procedure). Ref: decision 018, ml area.
- [ ] 1.2 Run `scripts/e2e_check.py` against the local service. Evidence: the pass table in the commit body. Ref: decision 019.

## 2. Measure (after the gate)

- [ ] 2.1 Measure once as `2024Q4-eval-v8` with the three repeats of the high-risk subset. Record the measured commit and freeze the run. From `eval-v8` 5.1. Evidence: `evidence/evaluation-runs/2024Q4-eval-v8/summary.json` and `eval/measured.json`. Ref: decision 018.
- [ ] 2.2 Judge each candidate by the amendment and write the verdict. Serve v3 by default only if it passes every gate. From `eval-v8` 5.2. Evidence: the result section of the amendment and the `app/ai/serving.py` tests. Ref: decisions 016 and 018.
- [ ] 2.3 Write `docs/rationale/router-error-analysis.md`: the ten most frequent confusions with case ids, cause and kind of fix; accuracy by intent with the number of bases; a note on the intents with fewer than 10 bases; confidence against accuracy from the run. Cite `summary.json` fields only. Evidence: the page. Ref: ml area, decision 018.
- [ ] 2.4 Regenerate the metrics report. Update the README limits, REQ-0016 evidence and the evidence index. Add `eval-v8` and `train-v1` to the CI replay list if they verify offline. From `eval-v8` 5.3. Evidence: those files. Ref: ml area.

## 3. Robustness runs (after the gate)

- [ ] 3.1 Freeze the fault-injection run. From `robustness-evidence` 2.1. Evidence: `evidence/robustness/<run-id>/summary.json`. Ref: decision 019.
- [ ] 3.2 Freeze the load run (recorded answers, 0.5 vCPU, 1 GiB) and the small live run. From `robustness-evidence` 2.2. Evidence: `evidence/robustness/<run-id>/summary.json`. Ref: decision 019.
- [ ] 3.3 Write the four rationale pages (`failure-handling`, `capacity-and-latency`, `cost-guard`, `attack-coverage`). Update the sizing page, the metrics catalog, the evidence index, REQ-0021, REQ-0026 and REQ-0053. From `robustness-evidence` 3.1. Evidence: those files. Ref: ml area.

## 4. Redeploy (after sections 2 and 3)

- [ ] 4.1 Add `SENTINEL_BRAND_NAME`, `SENTINEL_BRAND_ACCENT`, `SENTINEL_LLM_DAILY_BUDGET_USD`, `SENTINEL_LLM_PROMPT_VERSION` (v3 only if task 2.2 passes) and `SENTINEL_CHARGE_RANKER` (off) to `deploy/azure/deploy.sh` and its README. From `live-ops` 2.0. Evidence: the script and a dry run. Ref: decision 019.
- [ ] 4.2 Redeploy once from `main`. Check health, the `bundle_hash` against task 1.1, the model and prompt served, the new locale keys, the demo personas, the three demo cases in es-419 and pt-BR, `scripts/felix_replay.py --base-url <link>` and the phone layout. Save the KQL queries and record their aggregates. Update REQ-0035, REQ-0050 and the README deployment line. From `live-ops` 2.1. Evidence: the check output and `deploy/azure/queries.kql`. Ref: decision 019.
- [ ] 4.3 Run `scripts/e2e_check.py` against the link. Evidence: the pass table. Ref: decision 019.

## 5. Close (after section 4)

- [ ] 5.1 Regenerate `site/numbers.json` and update the slides with the frozen numbers. From `pitch-site` 4.1. Evidence: the numbers test passes. Ref: REQ-0030.
- [ ] 5.2 Review the README (links, numbers with their fields, limits). Add the last pull requests to the changelog. Check each row of the submission checklist. From `release` 4.1. Evidence: the diff and the checklist. Ref: decision 019.
- [ ] 5.3 Give the owner the exact `git tag v1.0-submission` and `gh release create` commands, after the redeploy. Evidence: the commands in `docs/build/delivery.md`. The owner runs them.
