---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Resolution live rehearsal (development)

Evidence: [`2024Q4-resolution-live-dev-v1`](../../../evidence/evaluation-runs/2024Q4-resolution-live-dev-v1/summary.json).

This note records the rehearsal of the live timing mode (task 2.3). The set is
the development resolution set: 56 cases in 14 situations. No sealed case is
read.

## What it proves

The live mode makes every router call a new live call. It ignores an existing
recording (`force_live`). The run records the latency per model call and per
conversation, and the cost per attempted case and per resolution.

| Field | Value |
|---|---|
| `timing.mode` | `live` |
| `timing.end_to_end` | `true` |
| `timing.per_call.n` | 56 |
| `timing.per_call.p50` / `p95` (ms) | 2439.66 / 5124.78 |
| `timing.per_conversation.p50` / `p95` (ms) | 2558.43 / 5220.92 |
| `timing.cost.per_attempted` (USD) | 0.00016 |
| `timing.cost.per_resolution` (USD) | 0.000558 |
| `spend.n` | 56 |
| `spend.spent_usd` | 0.008935 |
| `spend.cap_usd` | 1.0 |
| `spend.capped` | `false` |

## Cost

The run spent USD 0.008935 over 56 live calls. The cap is USD 1. The cap did
not stop the run.

## Result

Safe resolution is 16 of 56 for the baseline and for `router_v2`. This matches
the replay. The live mode changes the timing, not the outcome.

## Limit

The set is the development set. The live run on the frozen build is task 2.4.
The store stays a mock. The label is simulation with live model calls.
