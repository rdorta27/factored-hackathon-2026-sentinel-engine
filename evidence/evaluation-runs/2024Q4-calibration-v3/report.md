# Calibration run 2024Q4-calibration-v3

Development + validation, n=224. Cut-offs chosen on validation: `t_act` = 1.0, `t_abstain` = 0.0 (n=24 labels with confidence).

## Development (n=198, accuracy 0.9848)

| Confidence band | n | Accuracy |
|---|---|---|
| 0.95-1.00 | 197 | 0.9898 |

Act 0.202 · Clarify 0.7929 · Abstain 0.0051

## Validation (n=26, accuracy 0.9231)

| Confidence band | n | Accuracy |
|---|---|---|
| 0.95-1.00 | 24 | 1.0 |

Act 0.2692 · Clarify 0.6538 · Abstain 0.0769

Spend: USD 0.115591 over 182 live calls (cap 0.45).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Confidences recorded once with log-probabilities; cut-offs chosen on the validation split (018 amendment).
- Validation is descriptive: development was read by model selection and the prompt examples; eval-v8 remains the clean measurement.
