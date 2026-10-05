---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Final metrics report: router held-out measurement

This page reports on the frozen run [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json). The `report.md` file next to it is the generated table view. Every number below comes from that `summary.json`. The field paths are under `component` unless stated. The [metrics](metrics.md) page lists the metrics and rules. Decision [018](decisions/018-evaluation-acceptance.md) gives the acceptance rules, written before the run. The [evidence index](../../evidence/README.md) lists every run.

**Label of the measurement:** offline, simulation. The 405 cases are model-written text. They are not dataset rows and not production traffic ([018](decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing), [what is real](../architecture/what-is-real.md#numbers)). Nothing here is a production improvement.

**Scope:** the learned component is the intent router (GLM 5.3 Flash on both routes, reasoning low, 400-token cap, temperature 0), against the keyword baseline ([007](decisions/007-learned-component.md), [016](decisions/016-router-models.md)). If router v3 is merged, we generate this report again on `2024Q4-eval-v8` ([plan](../../team/router-v3-plan.md)). If not, v2 ships with the limit declared in section 8.

## 1. What was measured: n, mix, versions

| Block | n | Content |
|---|---|---|
| Main | 280 | 70 base cases × 4 variants (es-MX, es-CO, es-AR, pt-BR), same case ids for every version (`identical_set`) |
| Noisy twins | 50 | Perturbed copies of main cases: amount shift 12, date shift 12, self-correction 12, truncated name 14 |
| Attacks | 75 | 45 reach the model, 30 are decided by code (baseline only); 54 es-419, 21 pt-BR |
| End to end | 30 | System replay with mock Gold |
| Total | 405 | One seal, hash `27ad2f1b…` (`seal.hash`) |

Mix of the main block by intent (`case_mix.main.by_intent`): charge 76, missing 68, out_of_scope 68, person 68. We balanced the mix by design, to get sufficient cases per class. It is **not** the real contact mix, so the global accuracy is not a field estimate.

Versions: `baseline` (keywords), `router_v1` (prompt without examples), `router_v2` (prompt with 8 examples, `examples_v2.ids`). The models, routes and prices are in `versions.<version>.models`, `routes` and `prices`. 950 live calls cost USD 0.09247, against a cap of 0.3 (`spend`).

## 2. Headline results (REQ-0016, REQ-0020)

| Version | Accuracy | 95% interval | JSON failures | Cost per case (USD) | Latency p50 / p95 (ms) |
|---|---|---|---|---|---|
| baseline | 0.5393 | [0.425, 0.65] (descriptive) | 0/280 | 0 | 0.01 / 0.01 |
| router_v1 | 0.7429 | [0.6429, 0.8429] | 0/280 | 0.000044 | 1093 / 4225 |
| router_v2 | 0.9821 | [0.95, 1.0] | 0/280 | 0.00013 | 1079 / 4475 |

Source: `versions.<version>.breakdown.overall`, `cost_usd.total` / 280, `latency_ms`. The intervals are a cluster bootstrap over the 70 bases (2000 resamples). So the four variants of one base do not count as four independent cases.

Paired against the baseline on the same 280 cases (`paired.*`):

| Comparison | Fixed | Broken | Net | 95% interval of net share | Above zero |
|---|---|---|---|---|---|
| router_v1 vs baseline | 61 | 4 | +57 | [0.1107, 0.3] | yes |
| router_v2 vs baseline | 124 | 0 | +124 | [0.3286, 0.55] | yes |
| router_v2 vs router_v1 | 67 | 0 | +67 | [0.1429, 0.3357] | yes |

The four cases that v1 breaks are the four variants of base `ho-b56`.

## 3. Where the gain comes from, and where it fails

By intent (`versions.<version>.breakdown.by_intent`):

| Intent | n | baseline | router_v1 | router_v2 |
|---|---|---|---|---|
| charge | 76 | 0.9079 | 1.0 | 1.0 |
| person | 68 | 0.7647 | 0.9412 | 1.0 |
| out_of_scope | 68 | 0.4412 | 1.0 | 1.0 |
| missing | 68 | 0.0 | 0.0 | 0.9265 |

- **Most of the gain is in one intent.** `missing` (vague messages that need a clarifying question) is 0 of 68 for the baseline and for v1. The examples of v2 cover it, and v2 reaches 0.9265 [0.8088, 1.0]. This one class gives most of the difference from v1 to v2. All remaining errors of v2 are in it: 5 of 68 `missing` cases.
- **We count the failures. We do not hide them.** v2 has 5 wrong cases out of 280 (1.8%), all in `missing`. v1 has 72 wrong. v2 fixes 67 and breaks none. The baseline has 129 wrong. No router version had JSON failures or an unavailable model (`json_failures`, `unavailable`).
- **Known open gap:** greetings and similar openers. [Router v3](../../team/router-v3-plan.md) plans to close it. The sealed set does not measure it. This is the reason for v8.

## 4. Variability and robustness (REQ-0022)

- **Stability:** v2 ran three times on 25 bases (100 cases). The agreement is 0.9933 (`versions.router_v2.stability`). The baseline and v1 have no repeated runs. The baseline is deterministic, and v1 has no stability measurement. We report stability. It is not an acceptance rule.
- **Noisy twins (n = 50, descriptive):** no case changed its outcome under noise, for any version (`noisy.degradation_vs_twin`: broken 0, fixed 0). 50 cases cannot exclude a small effect. They only show that we saw none.
- **Intervals:** when an interval is wider than ±10 points, the table says "descriptive", and the number decides nothing ([018](decisions/018-evaluation-acceptance.md#decision), sizing basis). The overall interval of the baseline and its intervals per variant have that label.

## 5. Breakdown by language and country (REQ-0024)

`versions.router_v2.breakdown.by_variant` (n = 70 each):

| Variant | Accuracy | 95% interval | Net loss in shared bases |
|---|---|---|---|
| es-MX | 0.9857 | [0.9571, 1.0] | 0 |
| es-AR | 0.9857 | [0.9571, 1.0] | 0 |
| pt-BR | 0.9857 | [0.9571, 1.0] | 0 |
| es-CO | 0.9714 | [0.9286, 1.0] | 1 (`ho-b34`) |

v1 scores 0.7429 on every variant. The baseline goes from 0.5286 to 0.5714 across variants, descriptive only. The one gap in v2 is one base in es-CO: 1 of 70, against a limit of 4 (D6).

No breakdown: system outcomes by customer **segment**. The cases are written text with no customer record, so a segment breakdown of these results would be invented. The [segment breakdown report](../reports/req_0024_segment_breakdown_report.md) gives the dataset side: transaction volume and dispute eligibility per segment (eligibility 8.42% to 8.50% across Basic, Plus, Premium and Student, n = 4,425,008 transactions). It describes the data, not how the system answers each segment. So the comparison of service outcomes by segment that the brief asks for is still missing.

## 6. Outcome metrics of the system replay (REQ-0055)

Replay of the loop with mock Gold, `system.<version>`. Each row states its denominator.

| Metric | baseline | router_v1 | router_v2 | Denominator |
|---|---|---|---|---|
| Unsafe outcomes | 0 | 0 | 0 | 105 / 75 / 75 |
| Containment (no handoff) | 0.72 (54) | 0.68 (51) | 0.60 (45) | 75 attempted |
| Missed handoffs | 45 | 6 | 0 | cases that needed a human |
| Unnecessary handoffs | 8 | 2 | 2 | handoffs made |
| Safe automated resolution | 0 of 75 | 0 of 75 | 0 of 75 | 75 attempted |
| Cost per attempted case (USD) | 0 | 0.000049 | 0.000134 | 75 |
| Cost per successful resolution | not defined | not defined | not defined | no resolutions |
| Latency p50 / p95 (ms) | 0.71 / 0.93 | 971 / 3829 | 938 / 2721 | 105 / 75 / 75 |

How to read it:

- **Unsafe outcomes: 0/75 per router version, 0/105 for the baseline.** By the rule of three, the true rate is 3/75 = 4% or less, with 95% confidence. Zero on a small sample is not zero risk. `unsafe_outcomes.cases` lists each unsafe outcome. The lists are empty.
- **The baseline "wins" containment and loses safety.** Its higher containment (0.72) comes from fewer handoffs: 45 missed handoffs, the cases that needed a person and did not get one. v2 contains less (0.60) and misses none. Always read containment with the missed handoffs, never alone ([metrics](metrics.md#1-outcome)).
- **Safe automated resolution is 0 of 75 for every version.** This comes from the replay, not from the system: no single-turn case reaches a confirmed dispute, so no case can count as resolved. So this run **does not show** a safe-resolution rate, and the cost per resolution is "not defined". The resolution run below measures it. No ROI figure comes from this table (REQ-0057 stays a labelled projection).
- **Latency caveat:** the component latency comes from the recorded live calls (p50 about 1.1 s, p95 about 4.4 s). The system latency for the router versions also includes live model calls, but the note of the run says replay time ([018](decisions/018-evaluation-acceptance.md#result)). The sub-millisecond figures of the baseline are code only.

### Resolution run over the mock store (REQ-0055)

The final measurement is [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json): the same committed set of 56 cases in 14 situations, baseline and `router_v2` paired, replayed on the final loop after the chat-loop change. The summary records `measured_commit`. [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json), measured before that change, stays next to it as the reference. Both runs verify offline (`python3 -m eval.run verify 2024Q4-resolution-v2`, the same for v1, with the model pair of 016 in the environment). We checked both again on 2026-10-04. Both replays are simulations over a mock store, not field rates (decision 022).

| Metric | v1 baseline | v1 router_v2 | v2 baseline | v2 router_v2 | Denominator |
|---|---|---|---|---|---|
| Safe automated resolution | 16 (0.2857) | 16 (0.2857) | 16 (0.2857) | 16 (0.2857) | 56 attempted |
| Unsafe outcomes | 0 | 0 | 0 | 0 | 56 |
| Missed handoffs | 0 | 0 | 0 | 0 | 28 must-hand-off |
| Unnecessary handoffs | 0 | 0 | 0 | 0 | — |
| Containment | 0.5 | 0.5 | 0.5 | 0.5 | 56 attempted |
| Cost per attempted case (USD) | 0 | 0.00016 | 0 | 0.00016 | 56 |
| Cost per successful resolution (USD) | 0 | 0.000561 | 0 | 0.000561 | 16 resolutions |
| Latency p50 / p95 (ms) | 0.46 / 0.58 | 0.46 / 0.63 | 0.65 / 1.18 | 0.64 / 1.09 | replay |

- The chat-loop change (response language from the interface) changed **no outcome on this set**. v2 reproduces the counts of v1 case for case. This is why `verify` on v1 also matches on the final loop. We measured again because the loop changed, and because v2 has the breakdown below.
- The paired resolution difference is **0 of 56** in both runs (interval [0, 0], not above zero). By rule R3 of [022](decisions/022-resolution-acceptance.md), `router_v2` does **not** resolve more than the baseline. R1 (safe), R2 (no missed handoffs) and R4 (router unsafe) pass in both runs.
- Both versions resolve the same 16 cases (the four eligible situations, in four variants each). They refuse or hand off the rest. The cost per resolution is USD 0.000561 for `router_v2`, from the 8 recorded live calls. v1 recorded them under the USD 0.45 cap. The v2 replay made no live call.
- No ROI figure comes from this replay, other than the rate and the costs above. The projection is a separate, labelled page ([ROI](roi.md)).
- The set does not cover `Pending`: the mock store has no `Pending` row. The set covers `Refunded` as `status.reversed`.

#### Why the paired difference is 0: the policy ceiling

The gap run [`2024Q4-resolution-gap-v1`](../../evidence/evaluation-runs/2024Q4-resolution-gap-v1/summary.json) compares the baseline and `router_v2` case by case. It replays the recordings of `2024Q4-resolution-v2`. It makes no live call. The script is `sentinel-ai-core/eval/resolution_gap.py`.

| Case label | Count | Source field |
|---|---|---|
| Both resolve | 16 of 56 | `labels.both_resolve` |
| Both fail | 40 of 56 | `labels.both_fail` |
| Different | 0 of 56 | `labels.different` |

- **The ceiling is 16 of 56 cases** (`ceiling.<version>.resolvable`, `ceiling_share` 0.2857). Policy sets the ceiling: 16 cases may resolve, and 40 require a handoff or must not pass. The router does not set it.
- **Both systems resolve all 16 resolvable cases** (`ceiling.<version>.resolved` 16, `achieved_share` 1.0, `gap` 0). The paired difference is 0 because the baseline already reaches the ceiling. No resolvable case is left.
- **No case differs in outcome or in intent label** (`outcome_differs.count` 0, `intent_differs.count` 0). The stated cause is `ceiling` (`cause`). The set cannot separate the two systems on resolution.
- The router gain is in intent accuracy on the held-out component set (section 2). It is not a resolution gain on this set.
- **Limit:** 56 cases come from 14 situations. Four eligible situations appear in four variants each. The set is too narrow to show a resolution difference between the two systems. Task 1.4 of [`evidence-hardening`](../../openspec/changes/evidence-hardening/tasks.md) decides if a router-sensitive block is added under a new hash, or if this note closes the question.

### Breakdown by variant and country (REQ-0024, simulated)

`system.<version>.by_variant` and `by_country` of the v2 run. The group counts add up to the 56 totals. The interval resamples the 14 situations.

| Group | n | Safe resolution (baseline / router_v2) | 95% interval |
|---|---|---|---|
| es-MX | 16 | 0.25 / 0.25 | [0.0, 0.625] |
| es-CO | 6 | 0.3333 / 0.3333 | [0.0, 1.0] |
| es-AR | 6 | 0.3333 / 0.3333 | [0.0, 1.0] |
| pt-BR | 28 | 0.2857 / 0.2857 | [0.0714, 0.5714] |

| Group | n | Safe resolution (baseline / router_v2) | 95% interval |
|---|---|---|---|
| MX | 32 | 0.25 / 0.25 | [0.0, 0.625] |
| CO | 12 | 0.3333 / 0.3333 | [0.0, 1.0] |
| AR | 12 | 0.3333 / 0.3333 | [0.0, 1.0] |

Every group interval is wider than ±10 points, so **every group is descriptive**. This set does not show a disparity between variants or countries, and it does not exclude one. The baseline and `router_v2` have the same figures per group, because they resolve the same cases.

**We declare the segment. We do not invent it.** These system outcomes have **no** breakdown by customer segment. The resolution cases have no customer record, so there is no segment to group by. The [segment breakdown report](../reports/req_0024_segment_breakdown_report.md) covers the dataset side only. We cite it as dataset context, not as a measurement of how the system answers each segment.

### Country monitoring (REQ-0050)

`sentinel-ai-core/eval/monitor.py` aggregates the turn log of the v2 replay per country and language. The result is frozen in [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json). The workload is stated there: 256 chat turns in 888 records, the full replay (baseline and `router_v2`). It has the label **simulated**. It is not field behavior.

| Country | Language | Turns | Latency p50 / p95 (ms) | Escalations | Handoffs | Fallback turns | Cost (USD) |
|---|---|---|---|---|---|---|---|
| AR | es-419 | 28 | 0.79 / 1.29 | 8 | 8 | 0 | 0.001916 |
| AR | pt-BR | 28 | 0.91 / 1.41 | 8 | 8 | 0 | 0 |
| CO | es-419 | 28 | 0.79 / 1.28 | 8 | 8 | 0 | 0.001916 |
| CO | pt-BR | 28 | 0.84 / 1.41 | 8 | 8 | 0 | 0 |
| MX | es-419 | 72 | 0.78 / 1.31 | 12 | 12 | 0 | 0.00514 |
| MX | pt-BR | 72 | 0.82 / 1.43 | 12 | 12 | 0 | 0 |

- No group of this workload has a failed or timed-out step, or a fallback turn.
- The cost is under es-419 only because the understand records carry the session language **before** detection. The model also ran for pt-BR turns, on the strong route (the same 8 recordings).
- Aggregates only. The monitoring output holds no trace id, no session reference and no text. An unknown country goes to a separate group, `other`.

## 7. Justification of metrics, thresholds and splits (REQ-0017)

### Metrics

| Metric | Why this one |
|---|---|
| Accuracy of the intent label, with a paired net difference | The router makes one decision, so accuracy is what the comparison of the brief asks. The paired difference (bases fixed minus bases broken) answers REQ-0016 directly. It cannot hide a case that the new component breaks. |
| Cluster bootstrap over bases | The 4 variants of a base are not independent. A resample of the 70 bases gives honest intervals. A resample of 280 cases gives intervals that are too narrow. |
| Missed and unnecessary handoffs | The cost is not symmetric. A missed handoff leaves a customer who needs a person without one. An unnecessary handoff costs advisor time. We report them separately, never as one error rate. |
| Unsafe outcomes with denominator | A top metric of the brief. Reported as a count over attempts, with the rule-of-three bound. |
| Median and p95 latency, cost per case | An average hides the tail that causes abandonment ([metrics](metrics.md#rules-for-all-metrics)). The cost is the total over cases, never mixed with unit costs. |

Accuracy per class (F1) is not the primary metric, because the main block is balanced by construction. The accuracy per intent in section 3 serves the same purpose. It shows the one class that has the gain.

### Thresholds

Decision [018](decisions/018-evaluation-acceptance.md) fixed all thresholds **before** the run, in cases and not in percentages, so anyone can check them:

| Rule | Threshold | Why this value |
|---|---|---|
| D5 beats baseline | The interval of the paired net difference is fully above zero | A point gain with an interval that crosses zero is not evidence. 280 cases detect about 7 points with power 0.8 (McNemar). |
| D6 variants comparable | Net loss against the best variant: 4 of 70 or less | The 5-point tolerance of 016 is 3.5 cases of 70, rounded up. |
| D7 safety | 0 unsafe outcomes on 75 attacks | Zero tolerance. The bound of 4% is the honest reading of zero on 75. |
| "Descriptive" label | Interval wider than ±10 points | Such a number decides nothing. |

Result per rule: D4 router v2, D5 passes (+124, above zero), D6 passes (largest loss 1 of 70), D7 passes (0/75). Decision [018](decisions/018-evaluation-acceptance.md#result) gives the detail and the fields. We chose the model pair on development only ([016](decisions/016-router-models.md)). The held-out set did not influence it.

### Splits and leakage

1. **Development and held-out are disjoint.** Development holds 164 cases (`2024Q4-select-v2`, `split: development`). The held-out set holds 405 (`2024Q4-eval-v7`). The variants of one base stay on the same side (split by unit). The 10 old held-out cases moved to development after six measurements ([018](decisions/018-evaluation-acceptance.md#context)).
2. **Sealed before the measurement.** A hash seals the held-out set (`seal.hash`; `sentinel-ai-core/eval/cases/seal.json`). We measured it once, and `sentinel-ai-core/eval/measured.json` records that. The runner refuses a second measurement of the same seal.
3. **Isolated author.** The writer of the held-out set could not read the prompt, the development cases, the examples or the decisions on thresholds ([018](decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing)). The v2 examples (8, ids in `examples_v2.ids`) come from development cases only.
4. **The time split applies to the data pipeline, not to the router set.** The router cases are simulation with no timestamps, so a time split has no meaning for them. For the label universe from the dataset, the cut is 2025-07-01, enforced in code, with a leak check of 5611 of 5611 and no shared ids between development and held-out ([REQ-0017](../requirements/data-ml.md#req-0017), `evidence/evaluation/method.md`). The customer 360 runs also read only data before the cut ([evidence index](../../evidence/README.md#customer-360)).

## 8. Limits to state with these numbers (REQ-0013)

- **Model-written cases.** The author and the reviewer are Claude models with the same label definitions. No person reviewed the cases, and no Portuguese speaker is on the team. An accuracy of 0.98 shows agreement with those definitions, **not** field accuracy. A bias that the author and the reviewer share stays hidden.
- **Balanced mix, not real mix.** We designed the class shares. The overall accuracy does not apply to the real distribution of contacts.
- **Small samples.** 70 cases per variant (about ±7 points at 90% accuracy), 50 noisy twins, 100 cases for stability, 75 attacks. We do not claim strict equivalence between variants (about 500 per variant at ±5 points).
- **We measure safe resolution as a simulation only** (section 6, mock store, 56 cases). **No segment breakdown of system outcomes** exists (section 5: the cases have no customer record). The segment report covers the dataset only.
- **Mock Gold.** The replay does not read real Gold ([tasks](../../team/tasks.md) 3 and 4).
- **One model family,** one temperature, one seed. No production traffic, no drift.
- **Greeting gap:** the sealed set does not cover it. Router v3 plans it.

## 9. Reproduction

```
cd sentinel-ai-core
python3 -m eval.run verify 2024Q4-eval-v7
```

Checked on 2026-10-02, and again on 2026-10-04, with `SENTINEL_LLM_CHEAP_MODEL` and `SENTINEL_LLM_STRONG_MODEL` set to the pair of 016:

- The **component block** (sections 2 to 5) replays identically from the recordings.
- The **system block** (section 6) does **not** reproduce. `verify` reports "DIFFERS". The replayed system metrics differ from the frozen ones (for example, containment 1.0 instead of 0.60 for v2, and no cost).

The first text of [018](decisions/018-evaluation-acceptance.md#result) said that only spend and latency differ. That was wrong, and 018 now has a correction. So section 6 cites the frozen `summary.json` as it is, and nobody reproduced it independently here. We never edit the frozen run. A new measurement is a new folder.

**Cause found (2026-10-02, task 1.1).** Two effects, both in the harness, none in the recorded model answers:

1. **The comparison included latency.** At the freeze commit, `_comparable` removed only `spend`, not the wall-clock `latency_ms`. The frozen system latency for the router versions came from the live calls (p50 about 0.97 s). A replay makes no live call (p50 under 1 ms). So `verify` reported DIFFERS even at the freeze commit. A new `verify` at `3af2553` (the commit that froze `eval-v7`) shows that the system block differs **only** in `latency_ms`. A later commit added `_strip`, which excludes `latency_ms` from the comparison.
2. **The loop changed.** The system block replays the live application loop, not a frozen artifact. Commits after the freeze changed the loop: `a7e9b76` makes an offer on the first out-of-scope turn instead of a handoff, `cff4d99` hands off on the third, and `71f6446` answers "why?" follow-ups. The recordings did not change (`git diff 3af2553..HEAD -- app/ai/fixtures` is empty). So the frozen outcomes stay fixed, but containment, missed handoffs and cost change. The component block depends only on the cases and the recordings. This is why it still reproduces.

Consequence: the **system** block of a frozen run is reproducible only while the loop does not change. The `resolution-eval` runs record the commit of the loop (task 4.3), so their replay is reproducible. A later change of the loop needs a new run, not an edit.
