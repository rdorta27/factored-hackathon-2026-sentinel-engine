# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Plan: [router v3](../../../team/router-v3-plan.md). Paths are under `sentinel-ai-core/` unless stated.

## 1. Cases and rules

- [ ] 1.1 Inventory the uncovered first-message types and write development cases for each in the four variants, with expected intent and system outcome. Evidence: cases under `eval/cases/` and `tests/test_eval_cases.py`.
- [ ] 1.2 Write the 018 amendment: new metrics, kept gates, targets from development numbers of baseline and v2, spend cap, sizing; commit it before any v3 call. Evidence: the decision file and its commit order.

## 2. Prompt v3

- [ ] 2.1 Define each intent in the prompt and add the fewest development examples for openers, recorded in `eval/examples_v3.json`. Evidence: `tests/test_ai_router.py` that v3 example ids are development ids.
- [ ] 2.2 Iterate on development only and record each development run. Evidence: selection runs under `evidence/evaluation-runs/`.

## 3. Sealed set

- [ ] 3.1 Have an isolated author write the set, review and back-translate it, and record the provenance. Evidence: `eval/review/` notes.
- [ ] 3.2 Seal it with a new hash, leaving the v7 entry untouched. Evidence: `eval/cases/seal.json` and a test that the v7 hash is unchanged.

## 4. Measure and serve

- [ ] 4.1 Measure baseline, v2 and v3 once as `2024Q4-eval-v8`, recording the measured commit. Evidence: `evidence/evaluation-runs/2024Q4-eval-v8/summary.json` and `eval/measured.json`.
- [ ] 4.2 Judge the result by the amendment and write the verdict. Evidence: the amendment's result section.
- [ ] 4.3 If v3 passes, serve it with the loader guarantee and pin its example ids; otherwise keep v2. Evidence: `app/ai/serving.py` tests.
- [ ] 4.4 Run the resolution set on v3 in the same measurement, regenerate the metrics report on v8 (breakdown included) and update README and REQ-0016 evidence. Evidence: those files.
- [ ] 4.5 Run the existing test suite and report counts, including any failure. Evidence: pytest output in the commit body.
