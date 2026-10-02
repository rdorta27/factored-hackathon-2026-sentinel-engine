# Router model selection

Decision [016](../build/decisions/016-router-models.md).

## Choice

The learned router uses open-weight models served by Fireworks AI: a cheap model for frequent turns and a stronger one for ambiguous and Portuguese turns. Which models is decided by a rule written before measuring, on the same held-out cases as the keyword baseline.

## Why

- **The brief asks for a learned component compared with a baseline** and for justified choices (REQ-0016). A rule fixed in advance plus a frozen run is a justification; a model's reputation is not.
- **Cost does not decide here.** A router turn is about 300 input and 50 output tokens, so every candidate costs well under a cent per turn. That frees the choice to be made on measured quality.
- **Quality that matters for this job:** valid JSON every time, correct intent, and no drop in Portuguese, which the dataset never covers.
- **Open weights keep production portable:** the same model can run on Azure AI Foundry or Databricks later, without depending on the provider used to measure.
- **Two routes match cost to difficulty:** most turns are simple; only ambiguous and Portuguese ones pay for a larger model.

## The rule

Per route, the cheapest model that returns valid JSON in 100% of cases, is within 2 points of the best accuracy on that route, and does not lose more than 5 points in pt-BR against es-419.

## Alternatives rejected

- **Choosing by reputation:** not measurable, not defensible.
- **A closed commercial model as the default:** strong, but ties production to one vendor; open weights met the need at lower cost.
- **The largest model for every turn:** pays 10 to 60 times more for a classification task.

## In production

The chosen weights are served on Azure or Databricks, with per-route quotas, a spending cap and the keyword baseline as the fallback when the model is unavailable.

## On the slide

"We measured open-weight models against our keyword baseline on the same held-out cases and picked, per route, the cheapest one that kept valid JSON and Portuguese quality. Open weights mean production is not tied to a provider."

Results: fill from the frozen run once recorded; cite its `summary.json`, never hand-copied numbers.
