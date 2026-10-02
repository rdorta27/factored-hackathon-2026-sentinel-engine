# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [016](../../../docs/build/decisions/016-router-models.md). Paths are under `sentinel-ai-core/` unless stated.

## 1. Know the starting point

- [ ] 1.1 Find why `python3 -m eval.run verify 2024Q4-eval-v7` reports its system block as different: run it at the commit that froze `eval-v7` and compare fields. Evidence: a note in `docs/build/metrics-report.md` section 9 and a correction of the claim in `docs/build/decisions/018-evaluation-acceptance.md` if it is wrong.
- [ ] 1.2 List the situations the mock store allows (charge, rule, expected outcome) from `app/tools/gold.py` and the country policy files. Evidence: a table in the change's design or in the rules file of 4.1.

## 2. Runner

- [ ] 2.1 Add the `confirm` field to the case model and loader, with validation, and keep every existing case unchanged. Evidence: `tests/test_eval_cases.py` cases for the new field and for old files.
- [ ] 2.2 Send the confirmation turn in `run_case` when `confirm` is set and the reply is a `confirm_box`; stop on anything else. Evidence: `tests/test_eval_runner.py` for resolve, refusal-without-third-turn and single-turn cases.
- [ ] 2.3 Check that `system_metrics` counts the case as resolved and that a refused charge opened is listed as unsafe. Evidence: `tests/test_eval_metrics.py`.

## 3. Cases

- [ ] 3.1 Write 12 to 16 situations with four variants each, in `eval/cases/resolution.jsonl`, with country, charge, `confirm`, expected outcome and the handoff label. Evidence: the file and `tests/test_eval_cases.py` counting situations and outcomes.
- [ ] 3.2 Back-translate the pt-BR variants and record the check as in [017](../../../docs/build/decisions/017-portuguese.md). Evidence: a note under `eval/review/`.
- [ ] 3.3 Check that the set shares no ids with the development or sealed sets. Evidence: `tests/test_eval_cases.py`.

## 4. Rules and run

- [ ] 4.1 Write the acceptance rules in cases and commit them before any recording. Evidence: the commit order in `git log` and the decision file.
- [ ] 4.2 Add the run entry (baseline and router_v2, paired, clustered by situation, recordings in a directory under `eval/`) and its report. Evidence: `tests/test_eval_run.py` offline with fixtures.
- [ ] 4.3 Record the router answers once under the spend cap and freeze the run write-once. Evidence: `evidence/evaluation-runs/<run-id>/summary.json` with `spend` within the cap.
- [ ] 4.4 Verify the frozen run offline, reproducing every field except spend and latency. Evidence: `python3 -m eval.run verify <run-id>` output pasted in the commit body.

## 5. Report

- [ ] 5.1 Update `docs/build/metrics-report.md` section 6 with the new run, the label "simulation over a mock store", and the case and situation counts. Evidence: that file.
- [ ] 5.2 Update README limitations, REQ-0055 and REQ-0057 evidence, and task 7 in `team/tasks.md`. Evidence: those files.
- [ ] 5.3 Run the existing test suite and report counts, including any failure. Evidence: pytest output in the commit body.
