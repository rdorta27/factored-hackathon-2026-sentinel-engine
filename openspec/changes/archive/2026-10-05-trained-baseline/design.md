---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Representation:** character n-grams survive typos, accents and the mix of Spanish and Portuguese better than words, with 138 training cases. Text is masked and lower-cased first, the same as the router input.
2. **Splits:** train on `development`, tune on `validation`, test once on the v8 sealed set. `check_splits` already refuses a base in two splits. The v2 example bases are in `development`, so the router and the trained baseline see the same development data.
3. **Labels:** the `kind` values of contract v3 (`charge`, `status`, `missing`, `out_of_scope`, `person`), from the development cases of `router-v3`. The baseline predicts `kind` only, not subtypes or slots. The label set is fixed in the training run. If `router-v3` adds development cases before the seal, retrain and freeze a new training run.
4. **Reproducibility:** fixed seed, pinned scikit-learn version in the `eval` extra, model file hash in `summary.json`, and a `verify` that retrains and compares.
5. **Metrics:** accuracy, precision, recall and F1 per intent, with the cluster bootstrap over bases of 018.

## Risks

- 138 cases are few. Mitigation: report the validation score as descriptive; the sealed v8 result is the only claim.
- A version mismatch changes the model. Mitigation: pinned version and `verify`.

## Coordination with `router-v3` (2026-10-04)

6. **Labels come from `router-v3`.** The development cases for contract v3 are in `eval/cases/dev_v3.jsonl` (task 2.1 of `router-v3`). Train only after that task is done and its branch is merged here, and train again if the cases change before the seal.
7. **Do not commit `uv.lock`.** The repository does not use `uv`. Pin `scikit-learn` in the `eval` extra of `pyproject.toml`.
8. **Python.** If `python3 -m pytest` does not find pytest, use the full path of the Python interpreter.
9. **No wait for `eval-v8`.** Training reads development data only. The amendment of `eval-v8` names the trained baseline as a candidate and needs only its name and training split, so the two plans run in parallel.
