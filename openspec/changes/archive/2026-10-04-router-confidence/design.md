# Design

## Context

`PromptedLLMRouter` (`app/ai/llm.py`) calls an OpenAI-compatible endpoint through `HttpTransport` (`app/ai/transport.py`) with `response_format: json_object` and `reasoning_effort: low`, and parses one JSON object with the intent, language and not-mine claim. `UnderstandResult` carries no score. `serving.py` serves v2 with a baseline fallback. Cases have two splits (`development`, `held_out`); development has 164 cases over about 74 bases. Policy thresholds in `config/policy/*.yaml` are bank parameters per country and currency. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:** a measured confidence and two cut-offs chosen on data, behind a setting. **Non-Goals:** letting the model decide eligibility or actions.

## Decisions

1. **Spike before building.** One recorded call with `logprobs: true` and `top_logprobs` on the served model, with JSON output and low reasoning. If log-probabilities are absent or do not cover the label token, stop and write the result in [016](../../../docs/build/decisions/016-router-models.md).
2. **Confidence from the label token.** The probability mass of the chosen intent's first token among the intent alternatives, normalised over the four labels. Alternative: ask the model to state a confidence; rejected because self-reported numbers are not calibrated.
3. **Validation by base.** About a fifth of development bases move to `validation`, all variants together, before any fitting; the rule is written in an amendment to [018](../../../docs/build/decisions/018-evaluation-acceptance.md).
4. **Choice rule.** `t_act`: the lowest confidence at which validation accuracy of acted labels is at least the v2 held-out accuracy minus the 018 tolerance; `t_abstain`: the highest confidence below which accuracy is under one half. Both are rounded and recorded with their run.
5. **Where the cut-offs live.** A small router configuration file next to the examples, loaded by `serving.py`, with the run id; not the country policy files, because the cut-offs belong to the model, not to the bank.
6. **Clarify through the existing path.** A borderline or low label is treated as `missing`, so the existing clarification and its limit apply; no new reply variant.

## Risks / Trade-offs

- **Provider support:** the whole change depends on the spike; it stops cheaply if unsupported.
- **Small validation set:** about 15 bases; the choice is labelled descriptive and the sealed measurement decides.
- **More clarifications:** lowers unsafe action but may raise unnecessary questions; the 018 amendment counts both.
- **Calendar:** must land before the `eval-v8` seal; if late, `router-v3` measures without it.
