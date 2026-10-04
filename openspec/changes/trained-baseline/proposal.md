---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The learned component (the intent router) beats a keyword baseline in `2024Q4-eval-v7` (REQ-0016). A keyword list is a weak opponent, and a judge can read it as a straw man. The brief asks for "an appropriate baseline". A trained classical classifier, with a training split apart from the sealed set, is a stronger and more credible comparison. Diego (MLE at Factored) also asked for precision and recall per intent.

## What Changes

- **A trained baseline:** TF-IDF on character n-grams (3 to 5, accent-insensitive) and a logistic regression, one model for es-419 and pt-BR. It trains on the `development` split only (138 cases). It tunes its one parameter (regularization) on the `validation` split (26 cases). It never reads a held-out case.
- **A frozen training run:** `evidence/evaluation-runs/2024Q4-train-v1/` with the split ids, the parameter, the validation scores and a hash of the model file. The model file is committed (small, no data rows).
- **A candidate in `eval-v8`:** the runner loads the frozen model as a version named `trained_baseline`. It needs no model key and costs nothing per case.
- **Precision and recall per intent** for every version, in the runner summary and the metrics report.
- **Amendments:** [007](../../../docs/build/decisions/007-learned-component.md) adds the trained baseline. [018](../../../docs/build/decisions/018-evaluation-acceptance.md) (through the amendment of [`eval-v8`](../eval-v8/proposal.md)) compares the router with the stronger baseline; this change does not write it. [013](../../../docs/build/decisions/013-experiment-tracking.md) records the training run.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `evaluation-runner`: a trained baseline version, its training run, and precision and recall per intent.

## Impact

- `sentinel-ai-core/eval/` (a `train` command, a `TrainedBaseline` model behind `ModelPort`), `pyproject.toml` (scikit-learn in the `eval` extra), decisions 007, 013 and 018, the metrics report.
- Not served: the service keeps `router_v2` or v3 and the keyword fallback.

## Non-goals

- Serving the trained baseline.
- A larger model or more training data. The point is a fair, cheap comparison, not a better classifier.
- Changes to the keyword baseline.
