---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

The held-out evidence shows a gap that a judge can see. The router raises intent accuracy from 0.539 (baseline) to 0.982 (`router_v2`). Safe resolution stays at 16 of 56 for both, and the paired difference is 0 ([`resolution-v2`](../../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json)). Latency (p50 0.64 ms) and cost come from a replay, not from live calls. The sealed set has 405 cases but only 70 bases. The attack suite has 3 cases that pass only because the model is a stand-in.

This change turns each weak point into a measured and stated result. It cites REQ-0022, REQ-0055, REQ-0021, REQ-0013 and REQ-0023.

## What Changes

- **Resolution gap.** A replay script compares the baseline and `router_v2` on each resolution case. It states how many cases can resolve at all (the ceiling) and where the two differ. If the set hides the router, an isolated author writes a router-sensitive block, sealed under its own hash.
- **Live latency and cost.** The resolution runner gets a live timing mode with a spend cap. It records p50 and p95 per call and per conversation, and cost per attempted case and per resolution. The lab run waits for the code freeze (`post-freeze`).
- **Evidence strength.** Each summary reports the number of bases next to the number of cases. Intervals resample by base. A person checks 20 labels. The final measurement repeats three times and reports the range.
- **Failures as results.** A rationale page records the negative results. The three attack cases that pass on the stand-in model run against the real model. The limits page lists the known limitation of the attack suite.

## Capabilities

### New Capabilities
- `evidence-reporting`: how the evaluation reports its sample size, its live measurements and its negative results.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/eval/` (new `resolution_gap.py`, runner timing mode, `intervals.py`, `report.py`), `evidence/evaluation-runs/`, `docs/build/metrics-report.md`, `docs/rationale/`, `docs/requirements/`, `team/`, and the evidence index.

## Non-goals

- Changes to the prompt, the policy or the cut-offs. They invalidate the sealed measurement (decision 025).
- A second measurement of any sealed set.
- A new flow or a new learned component.
- A claim of production performance. All results stay labelled as simulation.
