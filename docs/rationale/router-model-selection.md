# Router model selection

Decision [016](../build/decisions/016-router-models.md).

## Choice

The learned router uses an open-weight model served by Fireworks AI: **GLM 5.3 Flash on both routes**. The team wrote the selection rule before the measurement. The selection used the development split only. The held-out set measured the result once.

## Why

- **The brief asks for a learned component against a baseline,** with justified choices (REQ-0016). A rule fixed in advance and a frozen run are a justification. The reputation of a model is not.
- **Cost does not decide here.** A router turn is about 300 input tokens and 50 output tokens. Every candidate costs much less than one cent per turn. So the choice can use measured quality.
- **Quality for this job:** valid JSON every time, the correct intent, and no loss in Portuguese. The dataset has no Portuguese.
- **Open weights keep production portable.** The same model can run on Azure AI Foundry or Databricks. Production does not depend on the provider of the measurement.

## The rule

Per route: the cheapest model that (a) returns valid JSON in 100% of cases, (b) is within 2 points of the best accuracy on that route, and (c) does not lose more than 5 points in pt-BR against es-419. The [amendment of 016](../build/decisions/016-router-models.md#amendment--selection-on-development-paired-pt-br-rule) makes the rule exact before the measurement.

## Result

Source: [`2024Q4-select-v2`](../../evidence/evaluation-runs/2024Q4-select-v2/summary.json), development split, n = 164. Fields are under `candidates.<model>` and `routes.heuristic.per_route_accuracy`.

| Candidate | Result | Field |
|---|---|---|
| gpt-oss-120b | Fails (a): many replies are not valid JSON | `candidates.<model>.json_failures` |
| DeepSeek V4.1 Flash | Fails (a) | `candidates.<model>.json_failures` |
| GLM-5.3 | Passes (a) and (c), fails (b) on the strong route | `candidates.<model>.breakdown` |
| **GLM 5.3 Flash** | Passes (a), (b) and (c) on both routes | `candidates.<model>.json_failures`, `pt_loss` |

GLM 5.3 Flash alone was more accurate than every cheap-and-strong pair on these cases. A larger model on the strong route did not help. The held-out result of this choice is in [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) and the [metrics report](../build/metrics-report.md).

The amendment listed fewer strong candidates than the original rule. Under the original rule, GLM 5.3 Flash passes on the strong route. The owner chose this reading, and decision 016 states the conflict.

## Alternatives rejected

- **Choose by reputation.** Not measurable, not defensible.
- **A closed commercial model as the default.** Strong, but it ties production to one vendor. Open weights met the need at a lower cost.
- **The largest model for every turn.** It costs 10 to 60 times more for a classification task.

## In production

The same weights run on Azure or Databricks, with quotas per route, a spend cap, and the keyword baseline as the fallback.

## On the slide

"We measured four open-weight models on development cases with a rule fixed before the measurement. One small model passed on every route and beat every pair. Then we measured it once on the sealed set."
