---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# charge-ranker / test-v1

This run measures the four charge-selection configurations on the test split, once ([025](../../../docs/build/decisions/025-charge-selector.md)).

- **Data type:** simulation. The descriptions are team-generated. The transactions are real Gold rows.
- **Rebuild:** `python -m eval.eval_charge_ranker --split test --run <new-folder>`, from `sentinel-ai-core/`. Do not edit this run.
- **Inputs:** [`data-v1`](../data-v1/README.md) (examples) and [`train-v1`](../train-v1/README.md) (weights). The summary records both hashes.
- **Ranges:** 95% ranges from a bootstrap that resamples customers.

## Configurations

| Name | What it is |
|---|---|
| `rules_fixed` | The parsers and the narrowing before `chat-start`. A frozen copy. |
| `rules_tuned` | `narrow` after `chat-start`, with the switch off. |
| `learned` | The same `narrow`, with the selector. This is the served path. |
| `LLM` | The model reads slots. Code narrows with them. A sample of 200 examples (`llm_sample`). |

## Cite these fields

| Question | Field |
|---|---|
| Does the selector rank the right charge first more often? | `configurations.<name>.all.right_first` |
| How often is a charge picked alone and wrong? | `configurations.<name>.all.wrong_automatic` |
| How often does the system ask? | `configurations.<name>.all.asks` |
| Is the right charge in the first three? | `configurations.<name>.all.right_in_top3` |
| Results by language, merchant name, family and amount in words | `configurations.<name>.breakdowns.*` |

## Result for the serving rule

- `learned` ranks the right charge first more often than `rules_tuned`. The 95% ranges do not overlap.
- `learned` has more wrong automatic picks than `rules_tuned`. The rules have none.
- The serving rule of decision 025 asks for no more wrong automatic picks. The rule fails. The switch stays off.

## Limits

- The `LLM` row uses 200 examples only. Its range is wide. Do not compare it with the others as an equal.
- Test lists of charges are longer than train lists. Test is harder than validation.
- The descriptions are team-generated. This is not production performance.
