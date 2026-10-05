---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Resolution gap v1: close with the ceiling note (task 1.4)

Evidence: [`2024Q4-resolution-gap-v1`](../../../evidence/evaluation-runs/2024Q4-resolution-gap-v1/summary.json).

## Decision

The owner closes task 1.4 with this note. The team does not write a new
router-sensitive resolution block. The ceiling explains the 0 paired
difference.

## Why

The gap run replays the baseline and `router_v2` on the 56 resolution cases
of `2024Q4-resolution-v2`. It makes no live call.

| Field | Value |
|---|---|
| `labels.both_resolve` | 16 of 56 |
| `labels.both_fail` | 40 of 56 |
| `labels.different` | 0 of 56 |
| `ceiling.baseline.resolvable` | 16 |
| `ceiling.router_v2.resolvable` | 16 |
| `ceiling.baseline.gap` | 0 |
| `ceiling.router_v2.gap` | 0 |
| `outcome_differs.count` | 0 |
| `intent_differs.count` | 0 |
| `cause` | `ceiling` |

Policy and data set the ceiling: 16 cases may resolve, and 40 require a
handoff or must not pass. Both systems resolve all 16 resolvable cases. The
baseline already reaches the ceiling, so no system can resolve more. The
paired difference is 0 for this reason.

## Limit

The set is narrow: 56 cases from 14 situations, and four eligible situations
in four variants each. The set does not measure a resolution gain of the
router. It measures that the router loses nothing on the ceiling. The router
gain is in intent accuracy on the held-out component set.

## Rule

A new resolution block would change the sealed claim. The team adds a block
only if the set hides the router. The set does not hide the router here. The
policy ceiling is the cause. No new case is added. Decision 022 stays
unchanged.
