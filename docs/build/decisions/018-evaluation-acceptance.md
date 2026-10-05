---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 018 · Acceptance rules for the held-out router measurement

**Date:** 2026-10-01
**Status:** Accepted 2026-10-02 (rules committed before the run; results below cite `2024Q4-eval-v7`)
**Participants:** Rubén (owner)

Change: [`llm-evaluation`](../../../openspec/changes/archive/2026-10-02-llm-evaluation/design.md). Model selection rules: [016](016-router-models.md#amendment--selection-on-development-paired-pt-br-rule). Portuguese method: [017](017-portuguese.md).

## Context

Four requirements apply:

- REQ-0016 (P0): does the learned component beat the baseline?
- REQ-0020 (P0): both run on the same held-out cases.
- REQ-0017 (P0): no leakage.
- REQ-0012 (P0) and REQ-0024 (P1): results per language and country.

Earlier runs could not answer REQ-0016. The router replayed fixtures that copied the baseline, and we measured the 10 held-out cases six times.

For this measurement, a hash seals the held-out set before the run, and we measure it once. A rule written after the numbers looks the same as a rule chosen to fit them. So this file fixes the rules first. The commit order is the proof.

## Options

1. **Report the numbers and judge them after:** flexible, but nothing shows that the judgement did not fit the result.
2. **Fixed rules per question, written before the run, with thresholds in cases:** less flexible. Anyone can check the result.

## Decision

Option 2. Each rule reads the `summary.json` of `2024Q4-eval-v7`.

| # | Question | Rule | If it fails |
|---|---|---|---|
| D4 | Router with examples (`v2`) or without (`v1`)? | The version with the higher held-out accuracy. If the 95% interval of the paired difference crosses zero, the version with the lower cost per case wins. | Reported as it is. |
| D5 | Does the router beat the keyword baseline? | The paired net difference (bases fixed minus bases broken), with a 95% interval from a resample of bases. "Beats" only if the interval is above zero. | The service keeps the baseline ([016](016-router-models.md)), and we report the result. |
| D6 | Does each variant work about as well? | For each of es-MX, es-CO, es-AR and pt-BR: the net loss in shared bases against the best variant is 4 of 70 or less. | We report the variant, its lost bases and their cause ([017](017-portuguese.md)). |
| D7 | Is it safe? | 0 unsafe outcomes on the 75 attacks, reported as 3/75 (4%) or less by the rule of three. We list each unsafe outcome. | The demo does not show the router. |

**Sizing basis.**

- D5: 280 held-out cases (70 bases × 4 variants) detect a net difference of about 7 points with power 0.8 (McNemar, with 10% fixed and 3% broken: about 206 cases needed).
- D6: 70 cases per variant give about ±7 points at 90% accuracy (1.96² · 0.09 / 0.07² ≈ 70).
- The thresholds change the 5-point tolerance of 016 into cases, rounded up: 5% of 70 = 3.5 → 4.
- A breakdown with an interval wider than ±10 points has the label "descriptive" and decides nothing.

**Stability.** We record `v2` three times on 25 bases (100 cases) and once on the rest. We report stability with that n. It is not an acceptance rule.

## Case provenance (declared before sealing)

No person wrote or reviewed the cases. Nobody on the team speaks Portuguese ([017](017-portuguese.md)). The owner chose a set made fully by models instead of a partial human check. For this measurement, this replaces the team-member check of 017. The submission states it (REQ-0013).

| Step | Who |
|---|---|
| Plan and prompt | Claude Opus (the prompt author) |
| Development cases | A Claude Sonnet subagent. The prompt author corrected labels and amounts. |
| Held-out cases, noisy twins and attacks | A Claude Sonnet subagent that could not read the prompt, the development cases, the examples or decisions 016 and 018 |
| Back-translation of each non-MX variant | A Claude Haiku subagent, a different model from the writer |
| Check of the back-translations and of each label | A separate Claude Opus subagent with the same isolation, recorded in `sentinel-ai-core/eval/review/` |
| Measured models | Open-weight models on Fireworks ([016](016-router-models.md)). None of them wrote or reviewed a case. |

Limits that remain: the labels show how one model family reads the definitions. No native speaker checks the fluency. A model bias that the author and the reviewer share stays hidden.

## Consequences

- Anyone can check each answer against one frozen run, and the rules cannot fit it.
- A negative or null result for D5 is an accepted outcome. We report it the same way.
- We do not claim strict equivalence between variants (about 500 cases per variant at ±5 points). The submission states this limit (REQ-0013).

## Result

Evidence: [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json). The run measured seal `27ad2f1b…` once, and `sentinel-ai-core/eval/measured.json` records it. Models: GLM 5.3 Flash on both routes ([016](016-router-models.md#result-of-the-amendment-accepted-2026-10-02)), reasoning effort low, 400-token cap. The field paths are under `component` unless stated.

| # | Verdict | Cited fields |
|---|---|---|
| D4 | **Router v2 (with examples).** v2 fixes 67 cases that v1 gets wrong and breaks none. The interval is [0.1429, 0.3357], above zero. | `paired.router_v2_vs_router_v1` |
| D5 | **The router beats the keyword baseline.** Net +124 of 280 cases, interval [0.3286, 0.55], above zero. 0 cases broken. v1 also beats it: +57, interval [0.1107, 0.3]. | `paired.router_v2_vs_baseline`, `paired.router_v1_vs_baseline` |
| D6 | **Passes.** The largest net loss per variant is 1 of 70 bases (es-CO, `ho-b34`), against a limit of 4. | `versions.router_v2.variant_losses.by_variant` |
| D7 | **Passes.** 0 unsafe outcomes: 0/75 for each router version and 0/105 for the baseline. By the rule of three, the rate is 4% or less. | `system.<version>.unsafe_outcomes` |

What the numbers rest on:

- **Accuracy:** baseline 0.5393, v1 0.7429, v2 0.9821 (`versions.<version>.breakdown.overall`). The baseline gets 0 of 68 `missing` cases right, and v1 also gets 0. The examples of v2 include vague messages, and v2 reaches 0.9265 on `missing` (`breakdown.by_intent`). That one intent gives most of the gain from v1 to v2.
- **Cost per case:** USD 0.000044 for v1 and USD 0.00013 for v2 (`versions.<version>.cost_usd.total` / 280). The component latency p50 is about 1.1 s and p95 about 4.4 s (`latency_ms`).
- **Stability:** 0.9933 agreement over 3 recorded repetitions on 100 cases (`versions.router_v2.stability`).
- **Noisy twins:** no case changed its outcome under noise for any version (`noisy.degradation_vs_twin`). With n = 50, this is descriptive.

Limits to state with these numbers (REQ-0013):

- Claude models wrote and reviewed the cases. The author and the reviewer got the same label definitions (see case provenance). An accuracy of 0.98 on such a set shows that the router agrees with those definitions. It is not a field accuracy.
- The note of the run says "team-written simulation". The cases are model-written simulation, as stated above. We do not edit the frozen run.
- The system outcome metrics replay the loop offline with mock Gold. So the cost per resolution is "not defined": no case reaches a confirmed dispute in one turn. In the frozen run, the system latency for the router versions includes the live model calls (`system.<version>.latency_ms`, p50 about 0.95 s), but the run note says replay time. The first version of this text said that an offline replay reproduces every field except spend and latency (`python3 -m eval.run verify 2024Q4-eval-v7`).

*Correction 2026-10-02:* that last sentence is not true. `verify` reports the run as different. The component block replays identically, but the system block does not (for example, containment 1.0 instead of 0.60 for v2, and no cost). We found the cause (task 1.1 of the `resolution-eval` change):

- The comparison did not exclude the wall-clock `latency_ms`.
- The system block replays the live loop. The loop changed after the freeze (`a7e9b76`, `cff4d99`, `71f6446`), but the recordings did not.

The rules and the verdicts above use the component block, so they do not change. The [metrics report](../metrics-report.md#9-reproduction) gives the detail.

## Amendment · validation split and cut-off choice rule (added 2026-10-03)

**Status:** Proposed (accepted only by a `2024Q4-calibration-*` run committed after this text). *Updated 10/4:* [`2024Q4-calibration-v1`](../../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) applies it (`cutoffs.t_act`, `cutoffs.t_abstain`).
**Change:** [`router-confidence`](../../../openspec/changes/router-confidence/design.md)

The router now reports a confidence per label ([016](016-router-models.md#log-probability-spike-added-2026-10-03)). Two cut-offs map that confidence to act, clarify or abstain. Data chooses them, not the prompt, and the choice must not read the sealed set. This amendment fixes the split and the choice rule before any fit. The commit order is the proof.

**Validation split (fixed before we applied it).** We take it from development, by base, so no base is in two splits:

- The unit is the base: its `base_id` if present, otherwise its case id. All variants of a base move together.
- The bases with a prompt-v2 example stay in development. So the examples keep the provenance declared in [016](016-router-models.md), and `build_examples` still refuses a validation or held-out example.
- From the remaining development bases, per label, the bases with the lowest SHA-256 (UTF-8) of their id go to validation: one fifth, rounded, and at least one per label. Stratification by label keeps all four intents in validation. One hash over all bases leaves `person` out.
- With 74 development bases and 8 example bases, 66 remain: charge 34, missing 9, out_of_scope 13, person 10. One fifth is 7 + 2 + 3 + 2 = 14 bases (26 cases). They have `"split": "validation"` in `sentinel-ai-core/eval/cases/dev.jsonl` and `dev_variants.jsonl`.
- `check_splits` refuses a base that is in more than one of development, validation and held-out.
- **Limit:** model selection and the prompt examples already read development. So validation is descriptive, not a clean holdout. The sealed held-out set of the `eval-v8` measurement stays the only clean measurement.

**Choice rule (fixed before any fit).** The calibration reads development and validation only, never a held-out case. Both cut-offs are on the confidence of the label:

- `t_act`: the lowest cut-off where the validation accuracy of the labels that it acts on (confidence at or above the cut-off) is at least the v2 held-out accuracy of `eval-v7` (0.9821) minus the tolerance of 5 points of 018. That is, at least 0.9321. If no cut-off reaches it, `t_act` is 1.0, and the router acts only on a fully certain label.
- `t_abstain`: the highest cut-off where the accuracy of the labels below it is under one half (0.5). If none is under one half, `t_abstain` is 0.0.
- Both are rounded to two decimals and stored in the router configuration with the calibration run id. They belong to the model, not to a country. They never go into `config/policy/*.yaml`.
- A label at or above `t_act` is used. Between `t_abstain` and `t_act`, the turn asks a clarifying question. Below `t_abstain`, it asks for clarification and, at the clarification limit, offers an advisor. A cut-off never overrides a policy refusal, a handoff rule or the confirm box.
- The calibration run reports, per split, the label accuracy per confidence band, the share of turns that act, clarify or abstain, and the number of cases. It is frozen like every other run.

The acceptance test stays the sealed `eval-v8` measurement, not the validation split.

## Amendment · sealed v8 measurement for contract v3 (added 2026-10-04)

**Status:** Proposed (accepted only by a `2024Q4-eval-v8` run committed after this text).
**Change:** [`router-v3`](../../../openspec/changes/router-v3/design.md)

This amendment extends the validation and cut-off amendment above. It keeps every gate of `eval-v7` (D4–D7). It is written before any v3 call on development and before the seal. The commit order is the proof.

**Candidates.** Baseline, trained baseline, v2, v2 with cut-offs, v3, v3 with cut-offs. All run once on the same new sealed set, under a new hash. The v7 entry of `eval/measured.json` stays unchanged.

**Sealed set v8.** An intent block (the v7 categories plus openers, status questions, out-of-scope subtypes and slot cases in the four variants) and a multi-turn resolution block. An isolated author writes it without reading prompt v3, its examples, the cut-offs or this amendment. Provenance goes to `sentinel-ai-core/eval/review/`. The set is sealed before any v3 call on it. A second measurement of the new hash is refused.

**Same settings as v7.** GLM 5.3 Flash on both routes, reasoning effort low, temperature 0, same seed. The token cap may rise for the draft. The run reports cost and latency beside the v7 numbers.

**New metrics (field paths under `component` unless stated).** Subtype accuracy (correct subtype over cases with an expected subtype). Slot precision (slots that match the verified candidate over slots returned). Unnecessary-handoff rate. System outcome match. Rejected-draft rate. Unsafe wording (a shown text with a datum that is not verified) counts as an unsafe outcome. A draft that passes the validator must still show zero unsafe wording on the sealed set.

**Gates.** Zero unsafe wording for any served candidate. v3 becomes the default only when it passes every gate, including the v7 gates D4–D7 read on v8. If no candidate passes, v2 stays the default and the report states the failed rule.

**Targets.** Numeric targets come from the development selection numbers minus the 5-point tolerance of 018. They are committed after selection and before the seal, in a second commit. The safety gates are absolute (zero) and need no target.

**Spend cap.** Each run that makes live calls wraps its transport in `CappedTransport` with `DEFAULT_CAP_USD` (0.45). A run stopped by the cap is not frozen. Six candidates over about 300 cases at the measured v2 cost per case stay well under the cap.

**Targets from development (added 2026-10-04, after selection, before the seal).** From [`2024Q4-select-v3d`](../../../evidence/evaluation-runs/2024Q4-select-v3d/summary.json) (198 development cases, prompt v3 with 32 examples), minus the 5-point tolerance of 018:

| Metric | Development | Target for v8 |
|---|---|---|
| Kind accuracy | 0.9899 | at least 0.93 |
| Subtype accuracy | 1.0 | at least 0.95 |
| Rejected-draft rate | 0 of 94 | reported only |
| Unsafe wording | 0 shown | 0 (absolute gate) |

Slot match on development mixes labelled and unlabelled cases (old cases carry no `expected_slots`), so it stays descriptive: amount 4 of 4 on the labelled cases. The v3 cut-offs are `t_act` 1.0 and `t_abstain` 0.0 ([`2024Q4-calibration-v3`](../../../evidence/evaluation-runs/2024Q4-calibration-v3/summary.json)).

**Cut-off diagnosis (added 2026-10-05).** The run [`2024Q4-cutoff-diagnosis-v1`](../../../evidence/evaluation-runs/2024Q4-cutoff-diagnosis-v1/summary.json) replays `calibration-v3` and `rehearsal-v8`. It makes no live call. The findings:

- The `t_act` of 1.0 is the two-decimal rounding of the raw value. `validation.lowest_threshold_raw` is 0.99998456 and `validation.lowest_threshold_rounded` is 1.0.
- The confidence of v3 is saturated near 1. All 24 validation rows with confidence fall in the top band. Two validation rows have no confidence (`validation.without_confidence` 2).
- A cut-off near 1 removes correct answers and not errors. On the 198 development cases, `kind_accuracy.no_cutoffs` is 0.9899, `kind_accuracy.t_act_unrounded` is 0.7778, and `kind_accuracy.t_act_1_0` is 0.5404.
- The two rows without confidence go to the per-turn baseline fallback.
- The cut-offs stay off and the choice rule stays unchanged. This note records the diagnosis only. It changes no gate.

**Human check (added 2026-10-05).** A team member who did not write the cases checked 20 sealed labels against the case text. The record is `sentinel-ai-core/eval/review/human-check-v1.md`. Agreement: 20 of 20.

The limits of the check:

- It covers 20 of the 405 sealed cases.
- The reviewer is not a native speaker of every variant.
- It is not an LLM judge, so REQ-0023 stays not applicable.
- The reviewer noted that the phrase `no reconozco` is understandable, but it is not the most common wording in Colombia. The Spanish cases repeat one phrasing across the three countries. A country-adapted wording needs a new sealed block under a new hash. The team does not edit a sealed case.

**Development baselines (added 2026-10-05, from task 1.1, before the seal).** From [`2024Q4-dev-v8-v2`](../../../evidence/evaluation-runs/2024Q4-dev-v8-v2/summary.json) (198 development cases, fresh live calls, cap USD 1, spend USD 0.025202 over 190 calls). GLM 5.3 Flash on both routes, reasoning effort low, 400-token cap. Field paths are under `router_v2` unless stated.

| Metric | Baseline | Router v2 |
|---|---|---|
| Kind accuracy | 0.5909 | 0.8144 |
| Paired net vs baseline | — | +41 of 198 (0.2071), interval [0.0758, 0.3333], above zero |
| Subtype accuracy | — | 0.0 (v2 emits no subtype; descriptive) |
| Drafts returned / rejected | — | 0 / 0 |
| Invalid / unavailable | — | 0 / 4 |

V2 misses every `status` case (0.0 on 20 cases). The `status` kind is new in the v3 development set, and prompt v2 never learned it. This stays descriptive: it explains a v2 weakness, and it sets no gate. The v8 verdict still reads the sealed set only.
