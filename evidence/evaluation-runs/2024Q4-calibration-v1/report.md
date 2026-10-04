# Calibration run 2024Q4-calibration-v1

Development + validation, n=164. Cut-offs chosen on validation: `t_act` = 0.86, `t_abstain` = 0.0 (n=26 labels with confidence).

## Development (n=138, accuracy 0.9058)

| Confidence band | n | Accuracy |
|---|---|---|
| 0.00-0.50 | 1 | 1.0 |
| 0.50-0.60 | 1 | 0.0 |
| 0.70-0.80 | 2 | 0.5 |
| 0.80-0.90 | 1 | 0.0 |
| 0.90-0.95 | 4 | 1.0 |
| 0.95-1.00 | 129 | 0.9225 |

Act 0.971 · Clarify 0.029 · Abstain 0.0

## Validation (n=26, accuracy 1.0)

| Confidence band | n | Accuracy |
|---|---|---|
| 0.80-0.90 | 1 | 1.0 |
| 0.90-0.95 | 2 | 1.0 |
| 0.95-1.00 | 23 | 1.0 |

Act 0.9615 · Clarify 0.0385 · Abstain 0.0

Spend: USD 0.021335 over 160 live calls (cap 0.45).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Confidences recorded once with log-probabilities; cut-offs chosen on the validation split (018 amendment).
- Validation is descriptive: development was read by model selection and the prompt examples; eval-v8 remains the clean measurement.
