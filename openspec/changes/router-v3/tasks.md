---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md), [ai](../../../docs/build/areas/ai.md). Decisions: [007](../../../docs/build/decisions/007-learned-component.md), [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Plan: [router v3](../../../team/router-v3-plan.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

## 1. Contract (first)

- [x] 1.1 Extend `UnderstandResult` to contract v3 with optional fields; the baseline and v2 still fit. Decision [024](../../../docs/build/decisions/024-model-wording.md) and the 007 update are done (branch `model-wording`). Evidence: `app/ai/port.py`, `app/ai/llm.py`, `app/ai/serving.py`, `tests/test_ai_router.py`.
- [ ] 1.2 Add the draft validator with placeholders and rejection reasons. Evidence: `app/ai/drafts.py`, `tests/test_drafts.py` with figure, name, date, promise, language and length cases.

## 2. Cases and rules

- [ ] 2.1 Write development cases for openers, status, subtypes and slots in four variants, never in the `validation` split. Evidence: `eval/cases/` and `tests/test_eval_cases.py`.
- [ ] 2.2 Extend the 018 amendment with the new metrics, targets from development numbers and the v8 spend cap, before any v3 call. Evidence: the decision file and its commit order.
- [ ] 2.3 Start the isolated author on the intent block of the sealed set. Evidence: `eval/review/` notes on provenance.

## 3. Prompt v3

- [ ] 3.1 Write prompt v3, its examples (`eval/examples_v3.json`) and its parser; serve it behind `SENTINEL_LLM_PROMPT_VERSION=v3`; iterate on development and freeze each selection run. Evidence: `app/ai/llm.py`, selection runs under `evidence/evaluation-runs/`.
- [ ] 3.2 Re-fit the cut-offs on v3 with the `router-confidence` code and rule. Evidence: a v3 calibration run.
- [ ] 3.3 Probe v3 with the real model through `eval/probe_v3.py`: development cases plus the Felix phrases 4 and 8. Report kind, subtype and slots against expected, raw and validated draft, rejection reason, language and cost. Evidence: `eval/probe_v3.py` and its markdown report.
- [ ] 3.4 Human review G2 with `chat-start`: Ruben reads the probe report and adjusts the prompt. Evidence: notes in `team/chat-manual-tests.md`.

## 4. Seal and measure (after the code freeze)

- [ ] 4.1 The isolated author writes the multi-turn block; review, back-translate and seal with a new hash; the v7 entry stays unchanged. Evidence: `eval/cases/seal.json` and a test.
- [ ] 4.2 Measure once as `2024Q4-eval-v8`: baseline, trained baseline, v2, v2 with cut-offs, v3, v3 with cut-offs. Evidence: `evidence/evaluation-runs/2024Q4-eval-v8/summary.json` and `eval/measured.json`.
- [ ] 4.3 Judge by the amendment, serve the best candidate that passes, update the metrics report, README, REQ-0016 and the evidence index. Evidence: those files and `app/ai/serving.py` tests.
