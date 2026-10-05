---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 025 · A learned selector ranks the charges

**Date:** 2026-10-04
**Status:** Proposed
**Participants:** Rubén (owner)

## Context

The riskiest step of the chat is the pick of the charge. A wrong pick opens a dispute on the wrong charge (REQ-0002, REQ-0003, REQ-0016).

Hand-written rules read the amount, the date and the merchant words. We tested them on 24 cases only. They miss some phrasings, for example amounts in words.

The brief asks for a learned part that we compare with a simple reference on held-out cases (REQ-0016, REQ-0017). The router is one learned part, and a model wrote its cases. A charge selector has exact labels: each description comes from one known transaction.

## Options

1. **Keep the rules.** No new risk. We have no second learned part.
2. **A small scoring model** (a logistic regression) on 20 to 30 clues from the existing parsers. It is cheap, fast and easy to explain.
3. **The language model picks the charge.** It reads the rows, so it breaks decision 024. Cost and latency are high.

## Decision

**Option 2.** We fix the rules below before any training. The commit order is the proof.

### Metrics

| Metric | Meaning |
|---|---|
| Right charge first | The top charge is the charge of the description. |
| Right charge in the first three | The charge of the description is in the top three. |
| Wrong automatic picks | The system picks a charge alone, and the charge is wrong. The denominator is every example. |
| Share that asks | The system shows the short list and asks. |

### Configurations

All four run on the same held-out set:

- `rules_fixed`: the current parsers with fixed order.
- `rules_tuned`: the parsers after `chat-start`.
- `learned`: the selector.
- `LLM`: the language-model reading, on a sample.

### Splits

| Split | Customers (hash of the customer id) | Time |
|---|---|---|
| train | 60% | before 2025-01-01 |
| validation | 20% | 2025-01-01 to 2025-06-30 |
| test | 20% | from 2025-07-01 |

- No customer id is in two splits.
- New phrasing families appear only in test.
- We measure the test set once.

### Threshold rule

1. Calibrate the scores on the train split only.
2. Set the picking threshold on the validation split only.
3. Choose the lowest threshold with 1% or less wrong automatic picks.
4. Record the threshold in the run.

### Serving rule

- The service does not use the selector unless `SENTINEL_CHARGE_RANKER` is on. The default is off.
- The switch turns on by default only if all of these are true:
  - the selector has no more wrong automatic picks than `rules_tuned` on the test set;
  - the selector ranks the right charge first more often than `rules_tuned`;
  - the owner approves.
- The switch can turn on only before the code freeze. After the freeze, the selector stays off, so `eval-v8` describes what the demo serves.

### Lock

The run records the hash of the model file, the seed, the family list and the threshold. The service refuses a model file with a different hash. The evaluation module never imports the training module.

## Consequences

- The labels are exact, and the descriptions are simulation (team-generated phrasing on real transactions). We never present the results as production performance.
- 77% of the charges in the development zone have no merchant name. The report splits results by "has a merchant name" and by language.
- Training reads raw transactions on this machine only. The repository holds no rows. The model file holds weights only.
- The confirm box, the policy and the router do not change.
- If the run is not frozen before the code freeze, the selector ships as an experiment and stays off.
