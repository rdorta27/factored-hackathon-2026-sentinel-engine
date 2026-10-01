# Evaluation run 2024Q4-eval-v6

Eval 2026-09-30+runner-v1 · labels 2024Q4-v1 (f55e1aed7e702a19) · n=44

## Component (router vs baseline)
### router: accuracy 0.8537 (n=41)
- charge: P 0.7931 R 1.0 F1 0.8846 (support 23)
- missing: P 0.0 R 0.0 F1 0.0 (support 6)
- out_of_scope: P 1.0 R 1.0 F1 1.0 (support 7)
- person: P 1.0 R 1.0 F1 1.0 (support 5)
- es-419: accuracy 0.8846 (n=26)
- pt-BR: accuracy 0.8 (n=15)
- stability: agreement 1.0 over 3 runs (n=41)
### baseline: accuracy 0.8537 (n=41)
- charge: P 0.7931 R 1.0 F1 0.8846 (support 23)
- missing: P 0.0 R 0.0 F1 0.0 (support 6)
- out_of_scope: P 1.0 R 1.0 F1 1.0 (support 7)
- person: P 1.0 R 1.0 F1 1.0 (support 5)
- es-419: accuracy 0.8846 (n=26)
- pt-BR: accuracy 0.8 (n=15)
- stability: agreement 1.0 over 3 runs (n=41)

## System
- safe resolution: 0/41
- containment share: 0.6341
- unsafe outcomes: 0/44
- latency p50/p95 ms: 0.57/1.67
- cost per attempted/resolution USD: 0.0001/not defined

## Failures
- none

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Router served by baseline-mirrored fixtures (no live model configured); router-vs-baseline delta is zero by construction.
- Small-sample limits apply per locale and class; held_out measured once in this run.
