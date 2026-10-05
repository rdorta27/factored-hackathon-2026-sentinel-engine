---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md), [analytics](../../../docs/build/areas/analysis.md). Decisions: [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [022](../../../docs/build/decisions/022-resolution-acceptance.md), [025](../../../docs/build/decisions/025-charge-selector.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

Depends on `eval-v8` (task 1.4 reports, task 3.1 rehearsal). Starts from `origin/main`. Runs before `pitch-site` closes. Tasks 2.4 and 3.5 need the code freeze and live in `post-freeze`.

## 1. Resolution gap

- [x] 1.1 Write `eval/resolution_gap.py`. It reads the recordings of `resolution-v2` and compares the baseline and `router_v2` on each case. It labels each case: both resolve, both fail, or different. It reports the ceiling of safe resolution. It makes no live call. Evidence: the script and a test.
- [x] 1.2 Run the script. Freeze the aggregates in `evidence/evaluation-runs/2024Q4-resolution-gap-v1/summary.json`. Add the run to `evidence/README.md` (Simulation, replay). Evidence: the run folder.
- [x] 1.3 Write the finding in `docs/build/metrics-report.md`: what the ceiling is and why the paired difference is 0. Evidence: the report section.
- [x] 1.4 Decide with the owner. If the set cannot separate the systems, an isolated author writes a router-sensitive resolution block (ambiguous, noisy and pt-BR situations). Review, back-translate and seal it under its own hash. If the ceiling explains the result, close this task with a note. Evidence: `eval/cases/` and `eval/review/`, or the note.

## 2. Live latency and cost

- [x] 2.1 Add a live timing mode to the resolution runner. It records p50 and p95 per call and per conversation, and cost per attempted case and per resolution. Use the existing spend cap. Evidence: `eval/runner.py`, tests with a fake transport.
- [x] 2.2 Label every latency and cost number as replay or live in the summary and in the report. Evidence: `eval/report.py`, a test.
- [x] 2.3 Rehearse the live mode on development data. Cap USD 1. Evidence: a development run and a note of its cost.
- [ ] 2.4 (`post-freeze`) Run the live mode once on the frozen build. Freeze it as `evidence/evaluation-runs/2024Q4-resolution-live-v1/`. Evidence: the run folder and the `/health` `bundle_hash`.

## 3. Evidence strength

- [x] 3.1 Add `bases` next to `n` in each summary and in the report. Evidence: `eval/metrics.py`, `eval/report.py`, tests.
- [x] 3.2 Resample the intervals by base in `eval/intervals.py`. Evidence: code and a test with a known interval.
- [ ] 3.3 A person checks 20 sealed labels against the case text. The reviewer is a team member who did not write the case. Record the agreement. Evidence: `eval/review/human-check-v1.md`.
- [ ] 3.4 Update decision 018 with the human check and its limits. Evidence: the decision file.
- [ ] 3.5 (`post-freeze`) Repeat the final measurement three times on the main block. Report the range for kind accuracy and for safe resolution. Evidence: the repeat block in the final summary.

## 4. Failures as results

- [x] 4.1 Write `docs/rationale/negative-results.md`: the charge selector (7 wrong automatic picks against 0 for the rules, switch off, decision 025), the confidence cut-offs of prompt v3 (see tasks 4.4 and 4.5), and any other rejected component. Link it from `docs/rationale/README.md`. Evidence: the page and the link.
- [ ] 4.2 Run the 3 attack cases that pass on the stand-in model against the real router model. Write a new adversarial run with `SENTINEL_WRITE_EVIDENCE=1`. Evidence: `evidence/adversarial/<run-id>/summary.json`.
- [ ] 4.3 Add the known limitation of the attack suite (category B), the three cases, the two model outputs without confidence in `calibration-v3` (one empty, one cut JSON; the per-turn baseline fallback covers them) and the two-decimal rounding of `t_act` (see task 4.4) to the limits page and to the README `## Limitations`. Evidence: the page and the README.

- [x] 4.4 Save the cut-off diagnosis as a replay-only script, `eval/cutoff_diagnosis.py`. It reads the committed recordings of `calibration-v3` and `rehearsal-v8` and makes no live call. It reports: the validation rows with and without confidence; the lowest threshold that meets the rule (0.99998456 before rounding, 1.0 after `round(t_act, 2)`); and the kind accuracy of v3 with `t_act` 1.0, with the unrounded threshold and without cut-offs. Freeze the aggregates as `evidence/evaluation-runs/2024Q4-cutoff-diagnosis-v1/summary.json`. Add the run to `evidence/README.md` (Simulation, replay). Do not change `calibration-v3`. Evidence: the script, a test and the run folder.
- [x] 4.5 Add a dated note to decision 018, after the v3 cut-off sentence: the `t_act` of 1.0 is the two-decimal rounding of 0.99998; the confidence of v3 is saturated near 1; a cut-off near 1 removes correct answers and not errors; cut-offs stay off and the rule stays unchanged. Cite the fields of the run of task 4.4. Evidence: the decision file.

## 5. Mocks in the documentation

- [x] 5.1 Review `docs/architecture/mocks.md` against the code: the mock list, the `gold_source` field and the three `passes_on_mock` cases. Fix any difference. Evidence: the page and a note of the checks.
- [ ] 5.2 Add the mocks and their limits to the slide on limits and to the README `## Limitations`. Link the page. Evidence: the README and the slide source in `site/slides/`.
- [ ] 5.3 Update the page after task 4.2: the three attack cases now run on the real model. Evidence: the page and the new adversarial run.

## 6. Requirements and team

- [x] 6.1 Update the cards of REQ-0022, REQ-0055, REQ-0021, REQ-0013 and REQ-0023 with the new evidence. Change a status only when its evidence exists. Evidence: `docs/requirements/`.
- [x] 6.2 Update the open work in `team/tasks.md` and the decision table in `team/pending-decisions.md`. Evidence: the two files.
