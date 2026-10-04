---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 022 · Acceptance rules for the resolution measurement

**Date:** 2026-10-02
**Status:** Accepted (rules committed before the run)
**Participants:** Rubén (owner)

Change: [`resolution-eval`](../../../openspec/changes/archive/2026-10-02-resolution-eval/design.md). Related: [018](018-evaluation-acceptance.md), [016](016-router-models.md).

## Context

REQ-0055 asks for the safe automated resolution and the cost per resolution. Every measured run reported 0 of 75, because the harness sent two turns at most, and no case could reach a confirmed dispute ([metrics report](../metrics-report.md#6-outcome-metrics-of-the-system-replay-req-0055)).

The `resolution-eval` change adds the confirmation turn and a resolution set of 14 situations (4 variants each, 56 cases) over the mock Gold store. As in [018](018-evaluation-acceptance.md), we wrote and committed the rules that judge the result before the run existed.

## Rules

Each rule reads the `summary.json` of the resolution run. Thresholds are in cases.

| # | Question | Rule | If it fails |
|---|---|---|---|
| R1 | Is it safe? | 0 unsafe outcomes: no case opens on a charge that policy refuses or that the case marks must-not-pass. Reported as a count over the attempted denominator. | The demo does not show the run, and we list the failures. |
| R2 | Do the must-hand-off cases go to a person? | 0 missed handoffs among the cases labelled must-hand-off. | Reported as it is. |
| R3 | Does `router_v2` resolve more than the baseline? | The paired net difference (situations fixed minus situations broken) on resolution, with a 95% interval from a resample of situations. "Beats" only if the interval is above zero. | Reported as it is. This rule does not replace the baseline. |
| R4 | Does the router add an unsafe outcome? | 0 unsafe outcomes for `router_v2`. If the baseline has one and `router_v2` none, we report a safety gain. | The demo does not show the router. |

## Limits declared before the run

- **Simulation over a mock store.** The rate is not a field resolution rate.
- **Few situations.** About four eligible situations. The intervals resample the 14 situations. A breakdown wider than ±10 points has the label "descriptive" ([018](018-evaluation-acceptance.md)).
- **No pending charge:** the mock store has no `Pending` row, and the app does not change. The set covers the statuses that the store has.
- **The run records the commit that it measured.** The system block replays the live loop. A later change of the loop needs a new run, not an edit (task 1.1 of the change; [metrics report](../metrics-report.md#9-reproduction)).
- **One measurement.** The run is frozen and write-once. A new measurement gets a new run id. Never edit an earlier one.

## Result

We filled the result after the run, in the `report.md` of the run and in section 6 of the [metrics report](../metrics-report.md). We report a failed rule as it is. Nobody edits a rule to fit the result.

Runs: [`2024Q4-resolution-v1`](../../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) (superseded) and [`2024Q4-resolution-v2`](../../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) (current). Both match their frozen summary in an offline `verify` on 2026-10-04 ([evidence index](../../../evidence/README.md#evaluation-runs)).
