# Cut-off diagnosis 2024Q4-cutoff-diagnosis-v1

Replay of 2024Q4-calibration-v3, 2024Q4-rehearsal-v8 · simulation · no live call.

## Validation rows

- rows: 26
- with confidence: 24
- without confidence: 2 (dev-fault-03, dv-b13-es-CO)
- lowest threshold that meets the rule: 0.9999845600455524 raw, 1.0 after round(t_act, 2)

## Kind accuracy of v3 (development)

| Configuration | n | Kind accuracy |
|---|---|---|
| no cut-offs | 198 | 0.9899 |
| t_act 1.0 | 198 | 0.5404 |
| t_act 0.9999845600455524 (unrounded) | 198 | 0.7778 |

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Replay of the committed recordings of calibration-v3 and rehearsal-v8: no live call.
- The raw cut-off is 0.99998456; round(t_act, 2) makes it 1.0. The confidence of v3 is saturated near 1.
- A cut-off near 1 removes correct answers and not errors. The cut-offs stay off and the rule stays unchanged (decision 018).
