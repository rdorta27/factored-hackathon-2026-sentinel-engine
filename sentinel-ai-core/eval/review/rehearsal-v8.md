---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Rehearsal v8 (development, every candidate)

Evidence: [`2024Q4-rehearsal-v8`](../../../evidence/evaluation-runs/2024Q4-rehearsal-v8/summary.json).
198 development cases. No sealed case read. GLM 5.3 Flash on both routes,
reasoning effort low, 400-token cap. Field paths are under `candidates.<name>`
unless stated.

## What it proves

Every candidate runs through the new metrics, the report and the spend cap.
The rehearsal judges nothing. The gates of the 018 amendment decide on the
sealed set only.

| Candidate | Kind accuracy | Subtype | Slot precision | Drafts rejected | Unsafe wording | Cost USD |
|---|---|---|---|---|---|---|
| `baseline` | 0.5909 | not defined | not defined | 0/0 | 0/0 | 0.0 |
| `trained_baseline` | 1.0 | not defined | not defined | 0/0 | 0/0 | 0.0 |
| `router_v2` | 0.8182 | 0.0 | 0.0588 | 0/0 | 0/0 | 0.026234 |
| `router_v2_cutoffs` | 0.8384 | 0.0 | 0.0588 | 0/0 | 0/0 | 0.026234 |
| `router_v3` | 0.9899 | 1.0 | 0.1395 | 0/94 | 0/94 | 0.119472 |
| `router_v3_cutoffs` | 0.5404 | 1.0 | 0.1395 | 0/94 | 0/94 | 0.119472 |

Paired `router_v3` vs `router_v2`: net +34 of 198 (0.1717), interval above
zero. Spend: USD 0.142788 over 388 live calls (cap 0.45). Time 873.9 s.

Two numbers need a limit:

- `trained_baseline` scores 1.0 because it trains on the development split.
  It is not a clean measure. The sealed set is.
- `router_v3_cutoffs` drops to 0.5404: the cut-offs send every low-confidence
  label to `missing`, so a case with the wrong low-confidence label no longer
  counts as correct. The trade is by design. The sealed set shows its cost.
- Slot precision is low because most development cases carry no
  `expected_slots` (018 amendment, descriptive).

## Prompt ablation (task 3.2)

Evidence: [`2024Q4-ablation-v8`](../../../evidence/evaluation-runs/2024Q4-ablation-v8/summary.json).
The same 198 development cases, prompt v3 with 0, 4, 8 and 32 examples.

| Config | Kind accuracy | Subtype | Cost USD | Latency p50 ms |
|---|---|---|---|---|
| `v3_no_examples` | 0.9848 | 1.0 | 0.023847 | 0.46 (replay) |
| `v3_4_examples` | 0.9747 | 1.0 | 0.034982 | 2401.05 |
| `v3_8_examples` | 0.9798 | 0.975 | 0.046462 | 2304.05 |
| `v3_32_examples` | 0.9899 | 1.0 | 0.119385 | 2119.98 |

Spend: USD 0.197 over 581 live calls (cap 1.0). Time 1647.1 s.
The `v3_no_examples` pass replayed the recordings of an earlier interrupted
attempt, so its latency is replay time, not live time. The true live cost of
that attempt was USD 0.023847; the ablation total across both attempts is
about USD 0.221.

The examples change kind accuracy by about one point. The ablation picks
nothing. The gates of the 018 amendment decide.
