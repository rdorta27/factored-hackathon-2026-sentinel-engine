---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# charge-ranker / train-v1

This run freezes the weights of the charge selector ([025](../../../docs/build/decisions/025-charge-selector.md)).

- **Data type:** simulation. The weights come from team-generated descriptions of real Gold transactions ([`data-v1`](../data-v1/README.md)).
- **Rebuild:** `SENTINEL_GOLD_DUCKDB=<path> python -m eval.train_charge_ranker`, from `sentinel-ai-core/`. It refuses to run if the rebuilt examples differ from `data-v1`.
- **Content:** `model.json` holds the weights, the temperature and the threshold. It holds no row and no personal data. `summary.json` records the hash of `model.json`.

## Order of use of the data

1. The weights come from the train split only.
2. The temperature comes from the train split only.
3. The threshold comes from the validation split only. It is the lowest value with 1% or less wrong automatic picks over every example.
4. The test split is not read (`test_split_read` is `false`).

## Cite these fields

| Question | Field |
|---|---|
| Which weights file does the service load? | `model_sha256` |
| Which threshold does the service use? | `threshold` |
| How does it do on validation? | `validation.right_charge_first`, `validation.wrong_automatic_picks` |
| Which penalty did we choose, and from what? | `penalty`, `penalties_tried` |

## Limits

- Validation is easy. The lists are short and most descriptions state the amount. Do not read `validation.*` as the result. The test run is the result.
- The three phrasing families of training are the only ones that the model saw. The test split adds two more.
