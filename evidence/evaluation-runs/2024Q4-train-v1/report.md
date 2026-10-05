# Training run 2024Q4-train-v1

Trained baseline: tfidf_char_ngrams_logistic_regression, 4171 features, labels charge, missing, out_of_scope, person, status.
Development n=198, validation n=26.
Selected C=3.0 · model sha256 `75f9bef2a3ff5325` · scikit-learn 1.9.1.

## Validation accuracy by C

| C | Accuracy |
|---|---|
| 0.1 | 0.3846 |
| 0.3 | 0.6538 |
| 1.0 | 0.7692 |
| 3.0 | 0.8462 |
| 10.0 | 0.8077 |
| 30.0 | 0.8077 |
| 100.0 | 0.7692 |
| 300.0 | 0.8077 |

## Validation per intent (descriptive)

| Intent | n | Precision | Recall | F1 |
|---|---|---|---|---|
| charge | 10 | 0.75 | 0.9 | 0.8182 |
| status | 0 | 0.0 | 0.0 | 0.0 |
| missing | 5 | 0.8333 | 1.0 | 0.9091 |
| out_of_scope | 9 | 1.0 | 0.6667 | 0.8 |
| person | 2 | 1.0 | 1.0 | 1.0 |

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Trained on development, tuned on validation. No held-out case was read.
- The validation scores describe only. The claim comes from the single sealed measurement of eval-v8.
- The development fit is a training score. Do not read it as performance.
- The validation split has no case for: status. Their scores are 0.0 by construction.
