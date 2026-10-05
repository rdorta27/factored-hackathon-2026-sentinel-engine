---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Negative results: components we rejected

A rejected component with a fixed rule shows rigor. This page records each rejected component, the rule that decided it and the evidence. The numbers come from frozen runs. Do not copy a number by hand.

## Charge selector

**Choice:** the learned charge selector stays off. The rules pick the charge.

**Why:** the selector ranks the right charge first more often than the rules. It also makes wrong automatic picks. The serving rule of [025](../build/decisions/025-charge-selector.md) requires no more wrong automatic picks than the rules. The rule fails.

**Evidence:** [`charge-ranker/test-v1`](../../evidence/charge-ranker/test-v1/summary.json). All four configurations run on the same held-out set of 5976 examples.

| Configuration | Right charge first | Wrong automatic picks | Asks |
|---|---|---|---|
| `rules_fixed` | `configurations.rules_fixed.all.right_first.rate` 0.9237 | `configurations.rules_fixed.all.wrong_automatic.count` 0 | 0.4694 |
| `rules_tuned` | `configurations.rules_tuned.all.right_first.rate` 0.9235 | `configurations.rules_tuned.all.wrong_automatic.count` 0 | 0.4726 |
| `learned` | `configurations.learned.all.right_first.rate` 0.9401 | `configurations.learned.all.wrong_automatic.count` 7 | 0.3059 |
| `LLM` | `configurations.LLM.all.right_first.rate` 0.89 | `configurations.LLM.all.wrong_automatic.count` 0 | 0.58 |

The selector wins at the first pick and loses on safety. Seven wrong automatic picks open a dispute on the wrong charge.

**Alternatives rejected:** keep the selector on with a warning; raise the threshold after the measurement; tune the rule. Decision 025 fixes the rule and the threshold before the measurement. A change after the measurement invalidates it.

**In production:** the switch `SENTINEL_CHARGE_RANKER` stays off. The demo and `eval-v8` use the rules.

**On the slide:** "We built a second learned part, measured it, and turned it off because it made a safety error the rules do not."

## Confidence cut-offs of prompt v3

**Choice:** the confidence cut-offs of prompt v3 stay off. The rule stays unchanged.

**Why:** the raw cut-off is 0.99998456. The two-decimal rounding makes it 1.0. The confidence of v3 is saturated near 1. A cut-off near 1 removes correct answers and not errors.

**Evidence:** [`2024Q4-cutoff-diagnosis-v1`](../../evidence/evaluation-runs/2024Q4-cutoff-diagnosis-v1/summary.json). The run replays `calibration-v3` and `rehearsal-v8`. It makes no live call.

| Field | Value |
|---|---|
| `validation.n` | 26 |
| `validation.with_confidence` | 24 |
| `validation.without_confidence` | 2 |
| `validation.lowest_threshold_raw` | 0.99998456 |
| `validation.lowest_threshold_rounded` | 1.0 |
| `kind_accuracy.no_cutoffs.kind_accuracy` | 0.9899 |
| `kind_accuracy.t_act_unrounded.kind_accuracy` | 0.7778 |
| `kind_accuracy.t_act_1_0.kind_accuracy` | 0.5404 |

The cut-off at 1.0 removes many correct answers: the kind accuracy falls from 0.9899 to 0.5404. The unrounded cut-off still falls to 0.7778. The two rows without confidence go to the per-turn baseline fallback.

**Alternatives rejected:** fix the rounding only. It is not enough: the unrounded cut-off still removes correct answers. Widen the validation set. It costs time and it changes the sealed claim.

**In production:** the cut-offs stay off. Decision [018](../build/decisions/018-evaluation-acceptance.md) records the diagnosis.

**On the slide:** "We measured the confidence cut-offs and turned them off. A cut-off near 1 removed correct answers, not errors."

## Other rejected components

| Component | Rule that decided it | Evidence |
|---|---|---|
| The language model picks the charge | It reads the transaction rows, so it breaks [024](../build/decisions/024-model-wording.md) | [025](../build/decisions/025-charge-selector.md), option 3 |
| Customer signals in the investigation | No signal predicts `is_fraud` or adds to `fraud_score` | [`customer-360/dev-signals-v1`](../../evidence/customer-360/dev-signals-v1/README.md) |
| A balance or product panel | The balance has no usable as-of date; blocked products have no transactions | [`customer-360/dev-v1`](../../evidence/customer-360/dev-v1/README.md) |
