---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 016 · Router models: open weights on Fireworks AI, chosen by measurement

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 10. Rationale for the presentation: [router model selection](../../rationale/router-model-selection.md).

## Context

The learned component is a prompted LLM router. It classifies the intent and the language. We compare it with a keyword baseline on the same held-out cases (REQ-0016, [007](007-learned-component.md)). At that date, its fixtures copied the baseline, so the measured difference was zero by construction until we recorded a live model.

The router uses an OpenAI-compatible chat API (`SENTINEL_LLM_BASE_URL`, one model per route: cheap and strong). Its only job is a short JSON reply: the intent, the language and the "not mine" claim.

A router turn is small: about 300 input tokens and 50 output tokens. So the cost difference between candidate models is a fraction of a cent, and measured quality can decide. The team has access to Fireworks AI.

## Options

1. **Choose a model by reputation:** fast, but not a justification.
2. **A closed commercial model:** strong, but it ties production to one vendor.
3. **Open-weight models on Fireworks AI, chosen by a rule declared before the measurement.**

## Decision

Option 3.

**Provider:** Fireworks AI serverless, OpenAI-compatible. The router needs only a base URL, a key and a model name per route. All candidates are open-weight models. Production can serve the same weights on Azure AI Foundry or Databricks (decision 12), without Fireworks.

**Candidates** (prices per million tokens, input / output, from the [Fireworks model library](https://fireworks.ai/models) on 2026-10-01; endpoint `https://api.fireworks.ai/inference/v1`):

| Route | Model | Model ID | Price |
|---|---|---|---|
| Cheap (frequent turns) | OpenAI gpt-oss-120b (starting point) | `accounts/fireworks/models/gpt-oss-120b` | 0.15 / 0.60 |
| Cheap | GLM 5.3 Flash | `accounts/fireworks/models/glm-5p3-flash` | 0.15 / 0.50 |
| Cheap | Nemotron Lightning 3.5 30B A3B | not looked up | 0.05 / 0.20 |
| Strong (ambiguous, pt-BR) | DeepSeek V4.1 Flash | `accounts/fireworks/models/deepseek-v4p1-flash` (the library shows `accounts/deepseek-ai/models/deepseek-v4p1-flash`; the first live call tells which one resolves) | 0.30 / 1.20, cached input 0.006 |
| Strong | GLM-5.3 | `accounts/fireworks/models/glm-5p3` | 1.40 / 4.40 |

Larger models (Qwen 3.8 Max, Kimi K3) cost 10 to 60 times more. They stay out unless the strong route fails the rule.

**Selection rule, fixed before the measurement.** Per route, the cheapest model that:

- (a) returns valid JSON in 100% of cases,
- (b) is within 2 points of the best accuracy on its route, and
- (c) does not score more than 5 points lower in pt-BR than in es-419.

**Measurement:** the same evaluation cases for the baseline and for each candidate, three repetitions. We record them once and freeze them as a new run with the model, the route, the prompt version, the tokens, the cost and the latency per turn ([013](013-experiment-tracking.md)). The recorded responses replay offline. The repository holds no key.

**Keys:** the measurement runs on the machine of the owner with a personal key that stays in `.env`. The public link keeps the keyword baseline ([019](019-azure-container-apps.md)) unless we create a separate, disposable Fireworks key with a spend cap for it. That key is only a Container App secret, and we revoke it after the evaluation.

## Consequences

- The evidence for the learned component shows a real difference against the baseline, positive or negative, with the cost and the latency per route.
- A rule and a frozen run justify the model choice, not a preference.
- A model call carries only masked customer text and a bounded window of turns. The fraud score and the identifiers never leave the service ([what the model never receives](../../rationale/model-data-minimization.md)). We check and state the data retention terms of Fireworks for serverless calls before the run.
- If no strong candidate meets the rule, we measure the larger models next. If the router cannot beat the baseline, the service keeps the baseline, and we report the result as it is.

## Amendment · selection on development, paired pt-BR rule

**Date:** 2026-10-01
**Status:** Proposed (accepted only by citing a `2024Q4-select-*` run committed after this text)
**Change:** [`llm-evaluation`](../../../openspec/changes/archive/2026-10-02-llm-evaluation/design.md)

We keep the rule above and make it exact for the run that applies it. We fixed each point below before we measured any candidate.

- **Where we measure:** the development split only (30 bases × 4 variants: es-MX, es-CO, es-AR, pt-BR, 120 cases). The held-out set never chooses a model or a route. We measure it once, after the choice, under [018](018-evaluation-acceptance.md).
- **Candidates:** gpt-oss-120b and GLM 5.3 Flash for the cheap route, DeepSeek V4.1 Flash for the strong route. Nemotron stays out. We measure GLM-5.3 and the larger models only if the strong candidate fails the rule.
- **D1 · cheap model:** conditions (a) and (b) above, on the turns that the route rule sends to the cheap route.
- **D2 · strong model:** (a) and (b), and (c) as a paired loss. Across the 30 development bases, count the bases where pt-BR is wrong and es-MX is right, minus the opposite. The result must be 3 or less. With 30 bases, 5 points is 1.5 cases. A value of 3 leaves room for chance in a set for the choice, not for claims.
- **D3 · route rule:** two candidates.
  - (i) The heuristic of `app/ai/llm.py`: Portuguese markers or more than 120 characters → strong.
  - (ii) pt-BR detected, or no baseline keyword matched → strong.
  - We keep the rule with the higher development accuracy. On a tie, we keep the one that sends fewer turns to the strong route. If neither reaches the accuracy of "every turn to the strong route" minus 2 points, every turn goes to the strong route.
- **Repetitions:** the selection runs once per candidate. We measure stability on the held-out set (018).

Consequence: one development run can reproduce the choice, and the held-out result cannot influence it.

### Result of the amendment (accepted 2026-10-02)

Evidence: [`2024Q4-select-v1`](../../../evidence/evaluation-runs/2024Q4-select-v1/summary.json) and [`2024Q4-select-v2`](../../../evidence/evaluation-runs/2024Q4-select-v2/summary.json), development split, n = 164. The fields are under `candidates.<model>` and `routes.heuristic.per_route_accuracy` of `2024Q4-select-v2`.

- **D1 · cheap model: GLM 5.3 Flash.** `json_failures.count` is 0, and it has the best cheap-route accuracy (0.7634, n = 131). gpt-oss-120b fails (a): 37 of 164 replies are not valid JSON.
- **D2 · strong model: no strong candidate met the rule.** DeepSeek V4.1 Flash fails (a): 9 of 164 replies are not valid. We then measured GLM-5.3, as this decision requires. It passes (a) and (c), with a pt-BR net loss of 1 of 30. It fails (b): 0.697 on the strong route against a best of 0.8485 (n = 33).
- **Resolution, chosen by the owner:** the original rule above says "per route, the cheapest model that" meets (a), (b) and (c), with no candidate list. The list of the amendment was narrower. Under the original rule, GLM 5.3 Flash meets all three on the strong route too: 0.8485, 0 invalid replies, and a pt-BR net loss of −1. So it serves both routes. We state the conflict here. We do not hide it. We did not measure Qwen 3.8 Max or Kimi K3, because they exceed the USD 0.50 budget.
- **D3 · route rule: heuristic**, the higher combined accuracy among the measured pairs. With one model on both routes, the rule only labels turns. It does not change the replies.
- **Observation, not a rule change:** on these cases, GLM 5.3 Flash alone (0.7805) beat every cheap-and-strong pair. A larger model on the strong route did not help.
- **Call settings fixed by the token probe:** reasoning effort `low` and a 400-token output cap. At 200 tokens and no reasoning setting, 32 of 154 gpt-oss replies were empty. We discarded those probe recordings before any selection run.
- **Spend:** USD 0.055 (select-v1) and USD 0.063 (select-v2), plus about USD 0.03 for the two probes.

### Served configuration (added 2026-10-02)

The app serves the pair chosen above, from `app/ai/serving.py`, when `SENTINEL_LLM_BASE_URL` and `SENTINEL_LLM_API_KEY` are set. Without them, it serves the keyword baseline.

- **Same as eval-v7:** GLM 5.3 Flash on every route, prompt `v2` with the eight development examples, route rule `heuristic`, reasoning effort `low`, a 400-token cap, temperature 0. A copy of the examples is in `app/ai/examples_v2.json`. A test keeps it equal to the eval loader, and the app checks it at startup.
- **Fallback:** a model call that fails after its retries (`ModelUnavailable`, an invalid JSON reply included) gets its answer from the keyword baseline for that turn. The customer sees no error. The turn log records the baseline as the model and `fallback` as the route. A fallback turn has the accuracy of the baseline (0.54 on the sealed set).
- **Timeouts:** 6 s and one retry per call. A failing model costs about 12 s before the baseline answers. eval-v7 recorded with 10 s and two retries. These two settings change the latency, not the replies.
- **A case that eval-v7 did not measure:** the model classifies a greeting alone as out of scope. The loop answers it with an offer and hands off on the third out-of-scope turn in a row. [Router v3](../../../team/router-v3-plan.md) addresses this gap in the classification.

### Log-probability spike (added 2026-10-03)

This is the feasibility check for [`router-confidence`](../../../openspec/changes/archive/2026-10-04-router-confidence/proposal.md) (task 1.1). The served model must return the alternatives of the label token before we build a confidence on it. One call per label, on the served configuration above.

**Request settings.** Endpoint `POST {SENTINEL_LLM_BASE_URL}/chat/completions`, model `accounts/fireworks/models/glm-5p3-flash` (both routes), prompt v2 with the eight development examples (`app/ai/examples_v2.json`), `response_format: {"type": "json_object"}`, `reasoning_effort: low`, `max_tokens: 400`, `temperature: 0`, and `logprobs: true` with `top_logprobs: 5`. Fireworks refuses `top_logprobs` above 5 with HTTP 400 (`top_logprobs must be between 0 and 5`), so 5 is the maximum. The four turns are development cases, one per label: `charge`, `missing`, `out_of_scope`, `person`.

**Result: supported.** All four calls returned HTTP 200, a valid JSON reply with the expected label, and `choices[0].logprobs.content` for every output token (29 to 31 tokens; 764 to 778 prompt tokens, 29 to 31 completion tokens, about USD 0.0005 for the four at the prices above). At the first token of the intent value, the top-5 list held the start of each of the four labels:

| Label | First token of the value | P(token) | Alternatives at that position |
|---|---|---|---|
| `charge` | `charge` | 0.9988 | `missing` 0.0009, `out` 0.0002, `person` 0.000008, `not` 0.000006 |
| `missing` | `missing` | 0.9947 | `out` 0.0036, `person` 0.0013, `charge` 0.0003, `unknown` 0.000005 |
| `out_of_scope` | `out` | 0.9990 | `missing` 0.0005, `person` 0.0003, `es` 0.00004, `charge` 0.00001 |
| `person` | `person` | 0.9997 | `missing` 0.0001, `charge` 0.00006, `out` 0.00005, `es` 0.00001 |

**What the build must handle:**

- The model writes `out_of_scope` as `out` + `_of` + `_scope`. So the confidence is the mass of the **first** token of the value over the four label starts, normalized, as design decision 2 states. In these four calls, the top-5 list always had all four label starts, so the denominator of the normalization was complete.
- Log-probabilities cover the content tokens only. The reasoning is not visible, and the label does not need it.
- The alternatives are tokens, so a token that is not a label (`not`, `unknown`, `es`) can be among them. The confidence uses the label starts only and normalizes them again. It never uses the raw top-5.

With log-probabilities confirmed on the served model, we built the rest of the `router-confidence` change. This note is its feasibility evidence. The cut-offs are in [`2024Q4-calibration-v1`](../../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) (`cutoffs.t_act`, `cutoffs.t_abstain`).
