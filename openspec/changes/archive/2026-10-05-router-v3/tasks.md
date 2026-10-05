---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md), [ai](../../../docs/build/areas/ai.md). Decisions: [007](../../../docs/build/decisions/007-learned-component.md), [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Plan: [router v3](../../../team/router-v3-plan.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

## 1. Contract (first)

- [x] 1.1 Extend `UnderstandResult` to contract v3 with optional fields; the baseline and v2 still fit. Decision [024](../../../docs/build/decisions/024-model-wording.md) and the 007 update are done (branch `model-wording`). Evidence: `app/ai/port.py`, `app/ai/llm.py`, `app/ai/serving.py`, `tests/test_ai_router.py`.
- [x] 1.2 Add the draft validator with placeholders and rejection reasons. Evidence: `app/ai/drafts.py`, `tests/test_drafts.py` with figure, name, date, promise, language and length cases.

## 2. Cases and rules

- [x] 2.1 Write development cases for openers, status, subtypes and slots in four variants, never in the `validation` split. Evidence: `eval/cases/` and `tests/test_eval_cases.py`.
- [x] 2.2 Extend the 018 amendment with the new metrics, targets from development numbers and the v8 spend cap, before any v3 call. Evidence: the decision file and its commit order.
- [x] 2.3 Start the isolated author on the intent block of the sealed set. Evidence: `eval/review/` notes on provenance.

## 3. Prompt v3

- [x] 3.1 Write prompt v3, its examples (`eval/examples_v3.json`) and its parser; serve it behind `SENTINEL_LLM_PROMPT_VERSION=v3`; iterate on development and freeze each selection run. Evidence: `app/ai/llm.py`, selection runs under `evidence/evaluation-runs/`.
- [x] 3.2 Re-fit the cut-offs on v3 with the `router-confidence` code and rule. Evidence: a v3 calibration run.
- [x] 3.3 Probe v3 with the real model through `eval/probe_v3.py`: development cases plus the Felix phrases 4 and 8. Report kind, subtype and slots against expected, raw and validated draft, rejection reason, language and cost. Evidence: `eval/probe_v3.py` and its markdown report.
- [x] 3.4 Human review G2 with `chat-start`: Ruben reads the probe report and adjusts the prompt. Evidence: notes in `team/chat-manual-tests.md`. Approved 2026-10-04 with no prompt changes; task 4.x waits for the code freeze.

## 4. Seal and measure (moved to `eval-v8`)

Tasks 4.1 (multi-turn block), 4.2 (`2024Q4-eval-v8` measurement) and 4.3 (judge and serve) moved to the `eval-v8` plan on 2026-10-04. This change builds the candidate; `eval-v8` judges it.
