---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [007](../../../docs/build/decisions/007-learned-component.md), [013](../../../docs/build/decisions/013-experiment-tracking.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Paths are under `sentinel-ai-core/` unless stated. Raw data stays outside git.

## 1. Rules first

- [x] 1.1 Write decision 025: the learned charge selector, the metrics (right charge first, right charge in the first three, wrong automatic picks, share that asks), the splits, the threshold rule and the serving rule. Update decision 007. Evidence: the decision files and their commit order.

## 2. Data

- [x] 2.1 Write the example generator for es-419 and pt-BR, with the phrasing families, fixed seed and no rows in git. Check the pt-BR templates by back-translation, as in 017. Evidence: `eval/charge_examples.py` and a test of the families.
- [x] 2.2 Build and freeze the splits: counts, hashes, seed and families, with no rows. Evidence: `evidence/charge-ranker/data-v1/summary.json`.

## 3. Model

- [x] 3.1 Write the clues, using the parsers of `app/ai/grounding.py`. Train on the train split only. Calibrate on train. Set the threshold on validation. Save the weights and their hash. Evidence: `app/ai/charge_ranker.py`, `eval/train_charge_ranker.py`, tests.
- [x] 3.2 Write the evaluation script. It compares the four configurations on the same set and reports by language and by "has a merchant name", with counts and 95% ranges. A test fails if it imports training code. Evidence: `eval/eval_charge_ranker.py` and the test.

## 4. Measure and serve

- [ ] 4.1 Wait for `chat-start` to merge (not for the code freeze), then measure the test set once. The result decides the switch before the freeze. Freeze the run. If `chat-start` is late, measure `rules_fixed` only and say so. Evidence: `evidence/charge-ranker/test-v1/summary.json`.
- [ ] 4.2 Add the switch `SENTINEL_CHARGE_RANKER` (off by default) and a test that "off" changes nothing. Turn it on by default only if the serving rule passes and the owner approves. Evidence: tests and the decision text.

## 5. Documents

- [ ] 5.1 Write `docs/rationale/charge-selector.md` in plain English. Update the ML area, the evidence index and the evidence of REQ-0016 and REQ-0017. Evidence: those files.
