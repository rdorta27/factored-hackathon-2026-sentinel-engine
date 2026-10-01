# Evaluation run 2024Q4-eval-v2

Eval 2026-09-30+runner-v1 · labels 2024Q4-v1 (f55e1aed7e702a19) · n=35

## Component (router vs baseline)
### router: accuracy 0.8125 (n=32)
- charge: P 0.7 R 1.0 F1 0.8235 (support 14)
- missing: P 0.0 R 0.0 F1 0.0 (support 6)
- out_of_scope: P 1.0 R 1.0 F1 1.0 (support 7)
- person: P 1.0 R 1.0 F1 1.0 (support 5)
- es-419: accuracy 0.8421 (n=19)
- pt-BR: accuracy 0.7692 (n=13)
- stability: agreement 1.0 over 3 runs (n=32)
### baseline: accuracy 0.8125 (n=32)
- charge: P 0.7 R 1.0 F1 0.8235 (support 14)
- missing: P 0.0 R 0.0 F1 0.0 (support 6)
- out_of_scope: P 1.0 R 1.0 F1 1.0 (support 7)
- person: P 1.0 R 1.0 F1 1.0 (support 5)
- es-419: accuracy 0.8421 (n=19)
- pt-BR: accuracy 0.7692 (n=13)
- stability: agreement 1.0 over 3 runs (n=32)

## System
- safe resolution: 0/32
- containment share: 0.7812
- unsafe outcomes: 0/35
- latency p50/p95 ms: 0.36/0.47
- cost per attempted/resolution USD: 0.0001/not defined

## Failures
- none

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Router served by baseline-mirrored fixtures (no live model configured); router-vs-baseline delta is zero by construction.
- Small-sample limits apply per locale and class; held_out measured once in this run.
