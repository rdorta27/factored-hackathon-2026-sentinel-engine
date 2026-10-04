# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Plan: [router v3](../../../team/router-v3-plan.md). Paths are under `sentinel-ai-core/` unless stated.

Depends on `router-confidence` and `evaluation-final` (both in `main`). The seal (3.2) waits for `flow-fixes`, `chat-start` and `trained-baseline` to merge, so `eval-v8` measures the final loop. Run `python3 -m pytest -q` after each group.

## 1. Cases and rules

- [ ] 1.1 Inventory the uncovered first-message types (greeting alone, greeting with a name, thanks and closing, small talk and identity, empty text, generic help, greeting followed by a request, out of scope without a keyword) and write development cases for each in the four variants, with expected intent and system outcome; never in the `validation` split of `router-confidence`. Evidence: cases under `eval/cases/` and `tests/test_eval_cases.py` (no shared bases across development, validation and held-out).
- [ ] 1.2 Extend the 018 amendment of `router-confidence` instead of writing a second one: add the unnecessary-handoff rate and the system outcome match, keep every v7 gate, set targets from development numbers of baseline and v2, the v8 spend cap and the sizing of the intent and resolution blocks; commit it before any v3 call. Evidence: the decision file and its commit order.

## 2. Prompt v3 and its cut-offs

- [ ] 2.1 Define each intent in one line, add the `status` label, add the fewest development examples for openers and status (`eval/examples_v3.json`), iterate on development only and record each run with log-probabilities. Add `status` cases to the development set in 1.1. Evidence: `tests/test_ai_router.py` (v3 example ids are development ids) and selection runs under `evidence/evaluation-runs/`.
- [ ] 2.2 Re-fit the cut-offs on v3 with the calibration code and the choice rule of `router-confidence`, unchanged, and freeze the calibration run; the v2 cut-offs are not reused for v3. Evidence: a v3 calibration run under `evidence/evaluation-runs/`.

## 3. Sealed set

- [ ] 3.1 Have an isolated author, who has not seen the prompts, examples, cut-offs or amendment, write the set: intent block with openers, multi-turn resolution block over the mock store, attacks and noisy twins, in the four variants; review and back-translate it and record the provenance. Evidence: `eval/review/` notes.
- [ ] 3.2 Seal it with a new hash, leaving the v7 entry untouched. Evidence: `eval/cases/seal.json` and a test that the v7 hash is unchanged.

## 4. Measure and serve

- [ ] 4.1 Measure once as `2024Q4-eval-v8`, intent and resolution blocks, with the breakdown by language and country: baseline, the trained baseline, v2 as served, v2 with its cut-offs, v3, v3 with its cut-offs; record the measured commit. Evidence: `evidence/evaluation-runs/2024Q4-eval-v8/summary.json` and `eval/measured.json`.
- [ ] 4.2 Judge each candidate by the amendment and write the verdict; serve the best that passes every gate with the loader guarantee and pinned example ids and cut-offs, otherwise keep v2. Evidence: the amendment's result section and `app/ai/serving.py` tests.
- [ ] 4.3 Regenerate the metrics report on v8, update README limitations and REQ-0016 evidence, add v8 to the CI replay list, and redeploy if the served configuration changed. Evidence: those files and the remote health check.
