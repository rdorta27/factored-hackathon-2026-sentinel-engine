---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Representation:** character n-grams survive typos, accents and the mix of Spanish and Portuguese better than words, with 138 training cases. Text is masked and lower-cased first, the same as the router input.
2. **Splits:** train on `development`, tune on `validation`, test once on the v8 sealed set. `check_splits` already refuses a base in two splits. The v2 example bases are in `development`, so the router and the trained baseline see the same development data.
3. **Labels:** the four intents of v2, plus `status` if `router-v3` adds it before the seal. The label set is fixed in the training run.
4. **Reproducibility:** fixed seed, pinned scikit-learn version in the `eval` extra, model file hash in `summary.json`, and a `verify` that retrains and compares.
5. **Metrics:** accuracy, precision, recall and F1 per intent, with the cluster bootstrap over bases of 018.

## Risks

- 138 cases are few. Mitigation: report the validation score as descriptive; the sealed v8 result is the only claim.
- A version mismatch changes the model. Mitigation: pinned version and `verify`.
