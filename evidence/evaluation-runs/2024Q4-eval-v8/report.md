# Held-out measurement 2024Q4-eval-v8 (v8)

Eval 2026-09-30+runner-v1 · commit 8ee4575 · n=536 cases · main 308, noisy 52, attacks 84, top-up 92.

Seals: v8 `3b4a472bb8071a24` (444 rows), v8b `ebdd937e5480014d` (92 rows).

## Main block by candidate

| Candidate | n | Kind accuracy | Subtype | Slots | Rejected drafts | Unsafe wording | Cost USD | Latency p50/p95 ms |
|---|---|---|---|---|---|---|---|---|
| baseline | 308 | 0.6916 | 0.0 | not defined | 0/0 | 0/0 | 0.0 | 0.01/0.01 |
| trained_baseline | 308 | 0.9026 | 0.0 | not defined | 0/0 | 0/0 | 0.0 | 0.11/0.14 |
| router_v2 | 308 | 0.8182 | 0.0 | 0.1444 | 0/0 | 0/0 | 0.04141 | 1474.2/4317.14 |
| router_v2_cutoffs | 308 | 0.8409 | 0.0 | 0.1444 | 0/0 | 0/0 | 0.04141 | 1474.2/4317.14 |
| router_v3 | 308 | 0.974 | 0.8971 | 0.2961 | 4/93 | 4/93 | 0.183692 | 2177.6/8616.76 |
| router_v3_cutoffs | 308 | 0.5097 | 0.9412 | 0.2961 | 4/96 | 4/96 | 0.186101 | 2177.6/7550.46 |

## Paired comparisons (main block)

- trained_baseline_vs_baseline: fixed 65, broken 0, net 65 of 308 (0.211), interval [0.1266, 0.3019], above zero: True
- router_v2_vs_baseline: fixed 39, broken 0, net 39 of 308 (0.1266), interval [0.0617, 0.2045], above zero: True
- router_v2_cutoffs_vs_baseline: fixed 46, broken 0, net 46 of 308 (0.1494), interval [0.0812, 0.2305], above zero: True
- router_v3_vs_baseline: fixed 88, broken 1, net 87 of 308 (0.2825), interval [0.1883, 0.3799], above zero: True
- router_v3_cutoffs_vs_baseline: fixed 48, broken 104, net -56 of 308 (-0.1818), interval [-0.3182, -0.0422], above zero: False
- router_v2_vs_trained_baseline: fixed 5, broken 31, net -26 of 308 (-0.0844), interval [-0.1591, -0.013], above zero: False
- router_v2_cutoffs_vs_trained_baseline: fixed 5, broken 24, net -19 of 308 (-0.0617), interval [-0.1266, 0.0], above zero: False
- router_v3_vs_trained_baseline: fixed 26, broken 4, net 22 of 308 (0.0714), interval [0.0097, 0.1364], above zero: True
- router_v3_cutoffs_vs_trained_baseline: fixed 1, broken 122, net -121 of 308 (-0.3929), interval [-0.4805, -0.3019], above zero: False
- router_v2_cutoffs_vs_router_v2: fixed 7, broken 0, net 7 of 308 (0.0227), interval [0.0, 0.0584], above zero: False
- router_v3_vs_router_v2: fixed 52, broken 4, net 48 of 308 (0.1558), interval [0.0714, 0.2435], above zero: True
- router_v3_cutoffs_vs_router_v2: fixed 28, broken 123, net -95 of 308 (-0.3084), interval [-0.4318, -0.1818], above zero: False
- router_v3_vs_router_v2_cutoffs: fixed 45, broken 4, net 41 of 308 (0.1331), interval [0.0552, 0.2143], above zero: True
- router_v3_cutoffs_vs_router_v2_cutoffs: fixed 21, broken 123, net -102 of 308 (-0.3312), interval [-0.4448, -0.2175], above zero: False
- router_v3_cutoffs_vs_router_v3: fixed 4, broken 147, net -143 of 308 (-0.4643), interval [-0.5617, -0.3669], above zero: False

## Attack block (n=84)

- baseline: kind 0.8571; unsafe wording 0/0 (none)
- trained_baseline: kind 0.881; unsafe wording 0/0 (none)
- router_v2: kind 0.9048; unsafe wording 0/0 (none)
- router_v2_cutoffs: kind 0.9048; unsafe wording 0/0 (none)
- router_v3: kind 0.8095; unsafe wording 0/5 (none)
- router_v3_cutoffs: kind 0.369; unsafe wording 0/6 (none)

## Top-up block (n=92)

- baseline: kind 0.3478; subtype not defined; unsafe wording 0/0
- trained_baseline: kind 0.5978; subtype not defined; unsafe wording 0/0
- router_v2: kind 0.6522; subtype not defined; unsafe wording 0/0
- router_v2_cutoffs: kind 0.6522; subtype not defined; unsafe wording 0/0
- router_v3: kind 0.7717; subtype not defined; unsafe wording 0/44
- router_v3_cutoffs: kind 0.3804; subtype not defined; unsafe wording 0/60

## High-risk repeats

- baseline: agreement 1.0 over 0 repetitions (n=308)
- trained_baseline: agreement 1.0 over 0 repetitions (n=308)
- router_v2: agreement 1.0 over 3 repetitions (n=308)
- router_v2_cutoffs: agreement 1.0 over 3 repetitions (n=308)
- router_v3: agreement 1.0 over 3 repetitions (n=308)
- router_v3_cutoffs: agreement 0.9259 over 3 repetitions (n=308)

Spend: USD 0.388858 over 946 live calls (cap 2.0). Prices: Fireworks model library, 2026-10-01 (decision 016).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Held-out v8 and top-up sets sealed by hash before measuring and measured once (decision 018).
- Six candidates of the 018 amendment: baseline, trained baseline, v2, v2 with cut-offs, v3, v3 with cut-offs.
- The high-risk subset is recorded three times. The cut-off variants reuse the recordings of their prompt.
