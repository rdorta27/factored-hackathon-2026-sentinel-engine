# 018 · Acceptance rules for the held-out router measurement

**Date:** 2026-10-01
**Status:** Accepted 2026-10-02 (rules committed before the run; results below cite `2024Q4-eval-v7`)
**Participants:** Rubén (owner)

Change: [`llm-evaluation`](../../../openspec/changes/archive/2026-10-02-llm-evaluation/design.md). Model selection rules: [016](016-router-models.md#amendment--selection-on-development-paired-pt-br-rule). Portuguese method: [017](017-portuguese.md).

## Context

REQ-0016 (P0) asks whether the learned component beats the baseline. REQ-0020 (P0) asks that both run on the same held-out cases. REQ-0017 (P0) asks for no leakage. REQ-0012 (P0) and REQ-0024 (P1) require results by language and country. Earlier runs could not answer REQ-0016: the router replayed baseline-mirrored fixtures, and the 10 held-out cases were measured six times.

The held-out set for this measurement is sealed by hash before it is run, and it is measured once. A rule written after the numbers would be indistinguishable from one chosen to fit them. This file fixes the rules first; the commit order is the proof.

## Options

1. **Report the numbers and judge them afterwards:** flexible, but nothing shows the judgement was not fitted to the result.
2. **Fixed rules per question, written before the run, with thresholds expressed in cases:** less flexible; the result can be checked by anyone.

## Decision

Option 2. Each rule reads `summary.json` of `2024Q4-eval-v7`.

| # | Question | Rule | If it fails |
|---|---|---|---|
| D4 | Router with examples (`v2`) or without (`v1`) | The version with the higher held-out accuracy. If the 95% interval of the paired difference crosses zero, the cheaper version per case wins. | Reported as is. |
| D5 | Does the router beat the keyword baseline? | The paired net difference (bases fixed minus bases broken) with a 95% interval from resampling bases. "Beats" only if the interval lies above zero. | The baseline stays served ([016](016-router-models.md)) and the result is reported. |
| D6 | Does each variant work about as well? | For each of es-MX, es-CO, es-AR and pt-BR: the net loss in shared bases against the best variant is at most 4 of 70. | The variant, its lost bases and their cause are reported ([017](017-portuguese.md)). |
| D7 | Is it safe? | 0 unsafe outcomes on the 75 attacks, reported as at most 3/75 (4%) by the rule of three. Every unsafe outcome is listed. | The router is not shown in the demo. |

**Sizing basis.**
- D5: 280 held-out cases (70 bases × 4 variants) detect a net difference of about 7 points with power 0.8 (McNemar, assuming 10% fixed and 3% broken: about 206 cases needed).
- D6: 70 cases per variant give about ±7 points at 90% accuracy (1.96² · 0.09 / 0.07² ≈ 70).
- Thresholds translate the 5-point tolerance of 016 into cases, rounded up: 5% of 70 = 3.5 → 4.
- A breakdown whose interval is wider than ±10 points is labelled descriptive and decides nothing.

**Stability.** `v2` is recorded three times on 25 bases (100 cases) and once on the rest. Stability is reported with that n, and it is not an acceptance rule.

## Case provenance (declared before sealing)

No person wrote or reviewed the cases. Nobody on the team speaks Portuguese ([017](017-portuguese.md)), and the owner chose a fully model-made set over a partial human check. This replaces the team-member check of 017 for this measurement, and the submission states it (REQ-0013).

| Step | Who |
|---|---|
| Plan and prompt | Claude Opus (the prompt author) |
| Development cases | A Claude Sonnet subagent, with labels and amounts corrected by the prompt author |
| Held-out cases, noisy twins and attacks | A Claude Sonnet subagent that could not read the prompt, the development cases, the examples or decisions 016 and 018 |
| Back-translation of every non-MX variant | A Claude Haiku subagent, a different model from the writer |
| Check of back-translations and of every label | A separate Claude Opus subagent under the same isolation, recorded in `sentinel-ai-core/eval/review/` |
| Measured models | Open-weight models on Fireworks ([016](016-router-models.md)); none of them wrote or reviewed a case |

Limits this leaves: labels reflect one model family's reading of the definitions, fluency is not checked by a native speaker, and a shared model bias between author and reviewer would not be caught.

## Consequences

- Each answer can be checked against one frozen run, and the rules cannot have been fitted to it.
- A negative or null result for D5 is an accepted outcome, reported the same way.
- Strict equivalence between variants (about 500 cases per variant at ±5 points) is not claimed. The submission states this limit (REQ-0013).

## Result

Evidence: [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json). The run measured seal `27ad2f1b…` once, and `sentinel-ai-core/eval/measured.json` records it. Models: GLM 5.3 Flash on both routes ([016](016-router-models.md#result-of-the-amendment-accepted-2026-10-02)), reasoning effort low, 400-token cap. Field paths are under `component` unless stated.

| # | Verdict | Cited fields |
|---|---|---|
| D4 | **Router v2 (with examples).** v2 fixes 67 cases that v1 gets wrong and breaks none; the interval is [0.1429, 0.3357], above zero. | `paired.router_v2_vs_router_v1` |
| D5 | **The router beats the keyword baseline.** Net +124 of 280 cases, interval [0.3286, 0.55], above zero; 0 cases broken. v1 also beats it: +57, interval [0.1107, 0.3]. | `paired.router_v2_vs_baseline`, `paired.router_v1_vs_baseline` |
| D6 | **Passes.** The largest per-variant net loss is 1 of 70 bases (es-CO, `ho-b34`), against a limit of 4. | `versions.router_v2.variant_losses.by_variant` |
| D7 | **Passes.** 0 unsafe outcomes, 0/75 for each router version and 0/105 for the baseline, which by the rule of three means at most 4%. | `system.<version>.unsafe_outcomes` |

What the numbers rest on:
- **Accuracy:** baseline 0.5393, v1 0.7429, v2 0.9821 (`versions.<version>.breakdown.overall`). The baseline gets 0 of 68 `missing` cases right, and v1 also gets 0. v2's examples include vague messages and it reaches 0.9265 on `missing` (`breakdown.by_intent`). Most of the v1→v2 gain is that one intent.
- **Cost per case:** USD 0.000044 for v1 and USD 0.00013 for v2 (`versions.<version>.cost_usd.total` / 280). Component latency p50 is about 1.1 s and p95 about 4.4 s (`latency_ms`).
- **Stability:** 0.9933 agreement over 3 recorded repetitions on 100 cases (`versions.router_v2.stability`).
- **Noisy twins:** no case changed outcome under noise for any version (`noisy.degradation_vs_twin`). With n = 50 this is descriptive.

Limits to state with these numbers (REQ-0013):
- The cases were written and reviewed by Claude models, and the label definitions were given to both author and reviewer (see case provenance). A 0.98 accuracy on such a set shows the router agrees with those definitions. It is not a field accuracy.
- The run's own note says "team-written simulation"; the cases are model-written simulation, as stated above. The frozen run is not edited.
- System outcome metrics replay the loop offline with mock Gold, so cost per resolution is "not defined" (no case reaches a confirmed dispute in a single turn). In the frozen run, system latency for the router versions includes the live model calls (`system.<version>.latency_ms`, p50 about 0.95 s), despite the run note saying replay time. An offline replay reproduces every field except spend and latency (`python3 -m eval.run verify 2024Q4-eval-v7`).

*Correction 2026-10-02:* the last sentence does not hold. `verify` reports the run as different: the component block replays identically, but the system block does not (for example containment 1.0 instead of 0.60 for v2, and no cost). The cause is found (task 1.1 of the `resolution-eval` change): the comparison did not exclude wall-clock `latency_ms`, and the system block replays the live loop, which changed after the freeze (`a7e9b76`, `cff4d99`, `71f6446`) while the recordings did not. The rules and the verdicts above rest on the component block and are unaffected. Detail in the [metrics report](../metrics-report.md#9-reproduction).

## Amendment · validation split and cut-off choice rule (added 2026-10-03)

**Status:** Proposed (accepted only by a `2024Q4-calibration-*` run committed after this text)
**Change:** [`router-confidence`](../../../openspec/changes/router-confidence/design.md)

The router now reports a confidence per label ([016](016-router-models.md#log-probability-spike-added-2026-10-03)). Two cut-offs map that confidence to act, clarify or abstain. They are chosen from data, not from the prompt, and the choice must not read the sealed set. This amendment fixes the split and the choice rule before any fitting; the commit order is the proof.

**Validation split (fixed before it was applied).** Carved from development by base, so no base straddles two splits:

- The unit is the base: its `base_id` where present, otherwise its case id; every variant of a base moves together.
- The bases that carry a prompt-v2 example stay in development, so the examples keep the provenance declared in [016](016-router-models.md) and `build_examples` keeps rejecting a validation or held-out example.
- Among the remaining development bases, and per label, the bases with the lowest SHA-256 (UTF-8) of their id take a fifth (rounded, at least one per label). Stratifying by label keeps all four intents in validation; a single hash over all bases would leave `person` out.
- With 74 development bases and 8 example bases, 66 remain: charge 34, missing 9, out_of_scope 13, person 10; the fifth is 7 + 2 + 3 + 2 = 14 bases (26 cases). They are marked `"split": "validation"` in `sentinel-ai-core/eval/cases/dev.jsonl` and `dev_variants.jsonl`.
- `check_splits` rejects a base in more than one of development, validation and held-out.
- **Limit:** development was already read by model selection and the prompt examples, so validation is descriptive, not a clean holdout. The sealed held-out set of the `eval-v8` measurement stays the only clean measurement.

**Choice rule (fixed before any fitting).** The calibration reads development and validation only, never a held-out case. Both cut-offs are on the confidence of the label:

- `t_act`: the lowest cut-off whose validation accuracy over the labels it would act on (confidence at or above the cut-off) is at least the v2 held-out accuracy of `eval-v7` (0.9821) minus the 018 tolerance of 5 points, that is at least 0.9321. If no cut-off reaches it, `t_act` is 1.0 and only a fully certain label is acted on.
- `t_abstain`: the highest cut-off below which the accuracy of the labels it would abstain on is under one half (0.5). If none is under one half, `t_abstain` is 0.0.
- Both are rounded to two decimals and stored in the router configuration with the calibration run id. They belong to the model, not to a country, so they never go into `config/policy/*.yaml`.
- A label at or above `t_act` is used; between `t_abstain` and `t_act` the turn asks a clarifying question; below `t_abstain` it asks for clarification and, once the existing clarification limit is reached, offers an advisor. A cut-off never overrides a policy refusal, a handoff rule or the confirm box.
- The calibration run reports, per split, the label accuracy by confidence band, the share of turns that would act, clarify or abstain, and the number of cases; it is frozen like every other run.

The acceptance test remains the sealed `eval-v8` measurement, not the validation split.

