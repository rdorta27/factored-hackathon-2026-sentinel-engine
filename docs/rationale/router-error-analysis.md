---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Router error analysis (v8)

This page lists the most frequent confusions of the intent router on the sealed v8 set. It is **descriptive and post hoc**. The cases are team-written simulation, never dataset rows ([what is real](../architecture/what-is-real.md#numbers)). The [analysis run](../../evidence/evaluation-runs/2024Q4-analysis-v8/summary.json) holds the numbers; the [frozen measurement](../../evidence/evaluation-runs/2024Q4-eval-v8/summary.json) holds the gates. The page names cases by id only. The case text stays in the sealed set.

The confusions come from `M1_errors.candidates.<name>.failures` of `2024Q4-analysis-v8`. That run replays the recordings of the frozen measurement, so it turns the rows that the measurement labelled `unavailable` into predictions ([018](../build/decisions/018-evaluation-acceptance.md#the-verify-limitation)).

## The ten most frequent confusions

The pair is `expected intent -> predicted intent`. The ids are the case ids.

| # | Model | Confusion | Cases | Case ids | Likely cause | Kind of fix |
|---|---|---|---|---|---|---|
| 1 | router_v2 | missing -> out_of_scope | 26 | v8i-23 to v8i-29 (four variants each, `v8i-28` in two) | A vague message names no charge, so v2 reads it as out of scope. | Prompt: the v2 examples cover vague messages, but the new `missing` cases are broader. |
| 2 | router_v2 | status -> out_of_scope | 16 | v8i-33 to v8i-35, v8i-52, v8i-53 | A status question is new to v2. It reads the message as out of scope. | Prompt: v3 learns `status`. |
| 3 | trained_baseline | status -> charge | 15 | v8i-33, v8i-35 to v8i-37, v8i-53 | The character n-grams of a status question overlap a charge message. | Data: the baseline has few `status` examples in development. |
| 4 | router_v2 | status -> charge | 12 | v8i-33, v8i-35 to v8i-37 | The same overlap. V2 never learned the `status` kind. | Prompt: v3 learns `status`. |
| 5 | trained_baseline | status -> out_of_scope | 8 | v8i-34, v8i-52, v8i-53 | A status question with no charge reference. | Data: more `status` cases in development. |
| 6 | router_v3 | status -> out_of_scope | 4 | v8i-52 (four variants) | The hardest `status` base for v3. | Prompt: one more `status` example of this shape. |
| 7 | trained_baseline | out_of_scope -> charge | 3 | v8i-44 (es-MX, es-CO, pt-BR) | The message names an account term that also appears in a charge message. | Data: more out-of-scope cases of this shape. |
| 8 | router_v2 | missing -> person | 2 | v8i-28 (es-AR, pt-BR) | The vague message asks about a person. | Prompt: the `person` rule needs the context of the vague message. |
| 9 | trained_baseline | out_of_scope -> missing | 2 | v8i-41-pt-BR, v8i-44-es-AR | The baseline sees no keyword for either class. | Data: more out-of-scope cases. |
| 10 | trained_baseline | status -> missing | 1 | v8i-34-pt-BR | The baseline sees no keyword. | Data: more `status` cases. |

The table reads fields of `2024Q4-analysis-v8`. The cause is the reading of the team. The kind of fix names prompt, policy or data.

## Accuracy by intent, with the number of bases

Source: `candidates.<name>.intent.confusion` of `2024Q4-eval-v8`, over the 308 main cases. The number of bases comes from the sealed set.

| Intent | Bases | Cases | router_v2 | router_v3 | trained_baseline |
|---|---|---|---|---|---|
| charge | 46 | 184 | 1.0 | 0.9946 | 1.0 |
| missing | 10 | 40 | 0.3 | 0.925 | 1.0 |
| out_of_scope | 7 | 28 | 1.0 | 1.0 | 0.8214 |
| person | 7 | 28 | 1.0 | 1.0 | 1.0 |
| status | 7 | 28 | 0.0 | 0.8571 | 0.1071 |

## The intents with fewer than 10 bases

`out_of_scope`, `person` and `status` have 7 bases each. `missing` has 10. The `charge` class has 46.

For `out_of_scope`, `person` and `status`, the interval is wider than ±10 points. The number is **descriptive** and makes no claim ([018](../build/decisions/018-evaluation-acceptance.md#decision)). A small base count cannot separate the models on these intents. The `status` figures show the same direction in all three models, but the set is too small to size the gap.

## The reading

- The served `router_v2` loses almost all its cases in two intents: `missing` (0.3) and `status` (0.0). Both are new or broad in the v8 set.
- `router_v3` closes most of the `missing` gap (0.925) and most of the `status` gap (0.8571), but it fails the served gates for other reasons ([018](../build/decisions/018-evaluation-acceptance.md#result-v8-added-2026-10-05)).
- The trained baseline is strong on `missing` and `charge`, and weak on `status` and `out_of_scope`. Its errors are different from the router errors. The [analysis run](../../evidence/evaluation-runs/2024Q4-analysis-v8/summary.json) reports the complementarity (`M4_complementarity`). A TF-IDF to LLM cascade is a **projection**, not a measurement.
