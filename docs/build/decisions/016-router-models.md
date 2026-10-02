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

**Keys:** the measurement runs on the owner's machine with a personal key that never leaves `.env`. The public link keeps the keyword baseline ([019](019-azure-container-apps.md)) unless a separate, disposable Fireworks key with a spending cap is created for it, stored only as a Container App secret and revoked after evaluation.

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

### Result of the amendment (accepted 2026-10-02)

Evidence: [`2024Q4-select-v1`](../../../evidence/evaluation-runs/2024Q4-select-v1/summary.json) and [`2024Q4-select-v2`](../../../evidence/evaluation-runs/2024Q4-select-v2/summary.json), development split, n = 164. Fields cited are under `candidates.<model>` and `routes.heuristic.per_route_accuracy` of `2024Q4-select-v2`.

- **D1 · cheap model: GLM 5.3 Flash.** `json_failures.count` is 0 and it has the best cheap-route accuracy (0.7634, n = 131). gpt-oss-120b fails (a), with 37 of 164 replies that are not valid JSON.
- **D2 · strong model: no strong candidate met the rule.** DeepSeek V4.1 Flash fails (a), with 9 of 164 replies invalid. GLM-5.3, measured next as this decision requires, passes (a) and (c), with a pt-BR net loss of 1 of 30. It fails (b): 0.697 on the strong route against a best of 0.8485 (n = 33).
- **Resolution, chosen by the owner:** the original rule above reads "per route, the cheapest model that" meets (a), (b) and (c), without a candidate list. The amendment's list was narrower. Under the original reading, GLM 5.3 Flash meets all three on the strong route as well: 0.8485, 0 invalid replies, and a pt-BR net loss of −1. It serves both routes. The conflict is stated here, not resolved silently. Measuring Qwen 3.8 Max or Kimi K3 was set aside because it exceeds the USD 0.50 budget.
- **D3 · route rule: heuristic**, the higher combined accuracy among the measured pairs. With one model on both routes, the rule only labels turns and does not change the replies.
- **Observation, not a rule change:** on these cases, GLM 5.3 Flash alone (0.7805) beat every cheap-plus-strong pair. Routing to a larger model did not help.
- **Call settings fixed by the token probe:** reasoning effort `low` and a 400-token output cap. At 200 tokens and no reasoning setting, 32 of 154 gpt-oss replies came back empty; those probe recordings were discarded before any selection run.
- **Spend:** USD 0.055 (select-v1) and USD 0.063 (select-v2), plus about USD 0.03 for the two probes.

### Served configuration (added 2026-10-02)

The app serves the pair chosen above, from `app/ai/serving.py`, when `SENTINEL_LLM_BASE_URL` and `SENTINEL_LLM_API_KEY` are set; without them it serves the keyword baseline.

- **Same as eval-v7:** GLM 5.3 Flash on every route, prompt `v2` with the eight development examples (a copy in `app/ai/examples_v2.json`, kept equal to the eval loader by a test and checked at startup), route rule `heuristic`, reasoning effort `low`, a 400-token cap, temperature 0.
- **Fallback:** a model call that fails after its retries (`ModelUnavailable`, including an invalid JSON reply) is answered by the keyword baseline for that turn, with no error to the customer. The turn log records the baseline as the model and `fallback` as the route. A fallback turn has the baseline's accuracy (0.54 on the sealed set).
- **Timeouts:** 6 s and one retry per call, so a failing model costs about 12 s before the baseline answers. eval-v7 recorded with 10 s and two retries; those two settings change latency, not the replies.
- **A case eval-v7 did not measure:** a greeting alone is classified out of scope. The loop answers it with an offer and hands off on the third out-of-scope turn in a row; the classification gap is the subject of [router v3](../../../team/router-v3-plan.md).
