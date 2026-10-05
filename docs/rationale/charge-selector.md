---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Charge selector

## The choice

A small learned model ranks the charges of the customer. We built it, measured it against the rules and left it off in the demo.

## Why

- The riskiest step of the chat is the pick of the charge. A wrong pick opens a dispute on the wrong charge.
- The router is a learned part, but a model wrote its test cases. The selector has exact labels: each description comes from one known transaction.
- The brief asks for a learned part that we compare with a simple reference on held-out data ([025](../build/decisions/025-charge-selector.md)).

## How we kept the test fair

| Rule | What it prevents |
|---|---|
| We fixed the metrics, splits and serving rule before training. | A rule shaped by a result. |
| Test customers never appear in training. | Leakage by customer. |
| The test dates are later than the training dates. | Leakage by time. |
| Two phrasing families appear only in test. | A model that learned our wording. |
| The test split is measured once, on a frozen weights file. | Repeated tries. |
| The evaluation module cannot import the training module. | Training on the test set. |

## What we found

Cite the fields of [`charge-ranker/test-v1`](../../evidence/charge-ranker/test-v1/summary.json).

| Question | Answer | Field |
|---|---|---|
| Does the selector rank the right charge first more often than the rules? | Yes. The 95% ranges do not overlap. | `configurations.<name>.all.right_first` |
| Does it ask less often? | Yes. | `configurations.<name>.all.asks` |
| Does it pick a wrong charge alone more often? | Yes. The rules never do. | `configurations.<name>.all.wrong_automatic` |

The serving rule asks for no more wrong automatic picks than the rules. The selector fails it. The switch `SENTINEL_CHARGE_RANKER` stays off.

## What to say on the slide

"We built a second learned part with exact labels. It ranks the right charge first more often than our rules. It also picks a wrong charge alone sometimes, so we keep it off. Safety decides, not accuracy."

## Limits

- The descriptions are team-generated. This is a simulation, not production performance.
- About 80% of the examples name no merchant, as in the data.
- The language-model row uses 200 examples. Its range is wide.
- Test is harder than validation. The lists of charges are longer.
- The pt-BR lines are team-written. No native speaker reviewed them.
