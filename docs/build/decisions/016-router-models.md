# 016 · Router models: open weights on Fireworks AI, chosen by measurement

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 10. Rationale for the presentation: [router model selection](../../rationale/router-model-selection.md).

## Context

The learned component is a prompted LLM router that classifies intent and language, compared with a keyword baseline on the same held-out cases (REQ-0016, [007](007-learned-component.md)). Its fixtures mirror the baseline, so the measured difference is zero by construction until a live model is recorded. The router speaks an OpenAI-compatible chat API (`SENTINEL_LLM_BASE_URL`, one model per route: cheap and strong) and its whole job is a short JSON reply: intent, language and the not-mine claim.

A router turn is small (about 300 input and 50 output tokens), so cost differences between candidate models are fractions of a cent: the choice can be made on measured quality. The team has access to Fireworks AI.

## Options

1. **Pick a model by reputation:** fast, but not a justification.
2. **A closed commercial model:** strong, but ties production to one vendor.
3. **Open-weight models on Fireworks AI, selected by a rule declared before measuring.**

## Decision

Option 3.

**Provider:** Fireworks AI serverless, OpenAI-compatible, so the router needs only a base URL, key and model name per route. All candidates are open-weight models, so production can serve the same weights on Azure AI Foundry or Databricks (decision 12) without depending on Fireworks.

**Candidates** (prices per million tokens, input / output, from the [Fireworks model library](https://fireworks.ai/models) on 2026-10-01; endpoint `https://api.fireworks.ai/inference/v1`):

| Route | Model | Model ID | Price |
|---|---|---|---|
| Cheap (frequent turns) | OpenAI gpt-oss-120b (starting point) | `accounts/fireworks/models/gpt-oss-120b` | 0.15 / 0.60 |
| Cheap | GLM 5.3 Flash | `accounts/fireworks/models/glm-5p3-flash` | 0.15 / 0.50 |
| Cheap | Nemotron Lightning 3.5 30B A3B | not looked up | 0.05 / 0.20 |
| Strong (ambiguous, pt-BR) | DeepSeek V4.1 Flash | `accounts/fireworks/models/deepseek-v4p1-flash` (the library listing shows `accounts/deepseek-ai/models/deepseek-v4p1-flash`; the first live call confirms which one resolves) | 0.30 / 1.20, cached input 0.006 |
| Strong | GLM-5.3 | `accounts/fireworks/models/glm-5p3` | 1.40 / 4.40 |

Larger models (Qwen 3.8 Max, Kimi K3) cost 10 to 60 times more and stay out unless the strong route fails the rule.

**Selection rule, fixed before measuring:** per route, the cheapest model that (a) returns valid JSON in 100% of cases, (b) is within 2 points of the best accuracy on its route, and (c) does not score more than 5 points lower in pt-BR than in es-419.

**Measurement:** the same evaluation cases for the baseline and every candidate, three repetitions, recorded once and frozen as a new run with model, route, prompt version, tokens, cost and latency per turn ([013](013-experiment-tracking.md)). The recorded responses replay offline; no key is stored in the repository.

**Keys:** the measurement runs on the owner's machine with a personal key that never leaves `.env`. The public link keeps the keyword baseline ([012](012-public-deployment.md)) unless a separate, disposable Fireworks key with a spending cap is created for it, stored only as a Space secret and revoked after evaluation.

## Consequences

- The learned-component evidence shows a real difference against the baseline, positive or negative, with cost and latency per route.
- The model choice is defensible by a rule and a frozen run, not by preference.
- Model calls carry only masked customer text and a bounded turn window; the fraud score and identifiers never leave ([what the model never receives](../../rationale/model-data-minimization.md)). Fireworks' data retention terms for serverless calls are checked and stated before the run.
- If no strong candidate meets the rule, the larger models are measured next; if the router cannot beat the baseline, the baseline stays served and the result is reported as is.

## Amendment · selection on development, paired pt-BR rule

**Date:** 2026-10-01
**Status:** Proposed (accepted only by citing a `2024Q4-select-*` run committed after this text)
**Change:** [`llm-evaluation`](../../../openspec/changes/llm-evaluation/design.md)

The rule above is kept and made precise for the run that applies it. Every point here is fixed before any candidate is measured.

- **Where it is measured:** the development split only (30 bases × 4 variants: es-MX, es-CO, es-AR, pt-BR, 120 cases). The held-out set is never used to choose a model or a route; it is measured once afterwards under [018](018-evaluation-acceptance.md).
- **Candidates:** gpt-oss-120b and GLM 5.3 Flash for the cheap route, DeepSeek V4.1 Flash for the strong route. Nemotron is left out. GLM-5.3 and the larger models are measured only if the strong candidate fails the rule.
- **D1 · cheap model:** (a) and (b) above, on the turns the route rule sends to the cheap route.
- **D2 · strong model:** (a) and (b), and condition (c) restated as a paired loss: across the 30 development bases, the bases where pt-BR is wrong and es-MX is right, minus the opposite, are at most 3. With 30 bases, 5 points is 1.5 cases; 3 leaves room for chance in a set used for choosing, not for claims.
- **D3 · route rule:** candidates are (i) today's heuristic in `app/ai/llm.py` (Portuguese markers or more than 120 characters → strong), and (ii) pt-BR detected or no baseline keyword matched → strong. The rule kept is the one with the higher development accuracy; on a tie, the one sending fewer turns to the strong route. If neither reaches the accuracy of sending every turn to the strong route minus 2 points, every turn goes to the strong route.
- **Repetitions:** selection runs once per candidate. Stability is measured on the held-out set (018).

Consequence: the choice is reproducible from one development run, and the held-out result cannot have influenced it.
