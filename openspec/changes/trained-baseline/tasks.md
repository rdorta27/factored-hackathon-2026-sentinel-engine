---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [007](../../../docs/build/decisions/007-learned-component.md), [013](../../../docs/build/decisions/013-experiment-tracking.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Paths are under `sentinel-ai-core/`. Merge before the rehearsal of `eval-v8` (task 3.1).

## 1. Rules first

- [x] 1.1 Amend 007 and 013 to add the trained baseline and its training run. Training reads development data only, so it does not wait for any other rule. The 018 amendment that names the trained baseline as a candidate belongs to [`eval-v8`](../eval-v8/proposal.md) (task 1.2), which needs only the name `trained_baseline` and the training split. Evidence: the decision files.

## 2. Training

- [x] 2.0 Merge `router-v3` once its task 2.1 is done, so the training data includes `eval/cases/dev_v3.jsonl`. Evidence: `git log` shows the merge.
- [ ] 2.1 Add `scikit-learn` to the `eval` extra with a pinned version, and a `python3 -m eval.run train` command that trains on `development` and tunes on `validation`. Evidence: `pyproject.toml`, `eval/train.py`, tests that refuse a held-out id.
- [ ] 2.2 Freeze `evidence/evaluation-runs/2024Q4-train-v1/` with the split ids, the parameter, validation scores and the model hash; add `verify`. Evidence: `summary.json` and a passing verify.

## 3. Runner

- [ ] 3.1 Load the frozen model as the `trained_baseline` version behind `ModelPort`. Evidence: tests.
- [ ] 3.2 Add precision, recall and F1 per intent with intervals to the runner summary. Evidence: tests and a dry run on development.

## 4. Documents

- [ ] 4.1 Update the ML area, the evidence index and REQ-0016 and REQ-0019 evidence. Evidence: those files.
