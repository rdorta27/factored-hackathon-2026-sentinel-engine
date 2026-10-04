# Final metrics report: router held-out measurement

Report on the frozen run [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`report.md` beside it is the generated table view). Every number below is read from that `summary.json`; field paths are under `component` unless stated. Catalog of metrics and rules: [metrics](metrics.md). Acceptance rules written before the run: [018](decisions/018-evaluation-acceptance.md).

**Label of the measurement:** offline, simulation. The 405 cases are model-written text, not dataset rows and not production traffic ([018](decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing)). Nothing here is a production improvement.

**Scope:** the learned component is the intent router (GLM 5.3 Flash on both routes, reasoning low, 400-token cap, temperature 0) against the keyword baseline ([007](decisions/007-learned-component.md), [016](decisions/016-router-models.md)). If router v3 lands, this report is regenerated on `2024Q4-eval-v8` ([plan](../../team/router-v3-plan.md)); if not, v2 ships with the limit declared in section 7.

## 1. What was measured: n, mix, versions

| Block | n | Content |
|---|---|---|
| Main | 280 | 70 base cases × 4 variants (es-MX, es-CO, es-AR, pt-BR), same case ids for every version (`identical_set`) |
| Noisy twins | 50 | Perturbed copies of main cases: amount shift 12, date shift 12, self-correction 12, truncated name 14 |
| Attacks | 75 | 45 reach the model, 30 are decided by code (baseline only); 54 es-419, 21 pt-BR |
| End to end | 30 | System replay with mock Gold |
| Total | 405 | One seal, hash `27ad2f1b…` (`seal.hash`) |

Main-block mix by intent (`case_mix.main.by_intent`): charge 76, missing 68, out_of_scope 68, person 68. The mix is balanced by design to get enough cases per class; it is **not** the real contact mix, so the global accuracy is not a field estimate.

Versions: `baseline` (keywords), `router_v1` (prompt without examples), `router_v2` (prompt with 8 examples, `examples_v2.ids`). Models, routes and prices are in `versions.<version>.models`, `routes`, `prices`. 950 live calls, USD 0.09247 against a cap of 0.3 (`spend`).

## 2. Headline results (REQ-0016, REQ-0020)

| Version | Accuracy | 95% interval | JSON failures | Cost per case (USD) | Latency p50 / p95 (ms) |
|---|---|---|---|---|---|
| baseline | 0.5393 | [0.425, 0.65] (descriptive) | 0/280 | 0 | 0.01 / 0.01 |
| router_v1 | 0.7429 | [0.6429, 0.8429] | 0/280 | 0.000044 | 1093 / 4225 |
| router_v2 | 0.9821 | [0.95, 1.0] | 0/280 | 0.00013 | 1079 / 4475 |

Source: `versions.<version>.breakdown.overall`, `cost_usd.total` / 280, `latency_ms`. Intervals are a cluster bootstrap over the 70 bases (2000 resamples), so the four variants of one base do not count as four independent cases.

Paired against the baseline on the same 280 cases (`paired.*`):

| Comparison | Fixed | Broken | Net | 95% interval of net share | Above zero |
|---|---|---|---|---|---|
| router_v1 vs baseline | 61 | 4 | +57 | [0.1107, 0.3] | yes |
| router_v2 vs baseline | 124 | 0 | +124 | [0.3286, 0.55] | yes |
| router_v2 vs router_v1 | 67 | 0 | +67 | [0.1429, 0.3357] | yes |

The four cases v1 breaks are the four variants of base `ho-b56`.

## 3. Where the gain comes from, and where it fails

By intent (`versions.<version>.breakdown.by_intent`):

| Intent | n | baseline | router_v1 | router_v2 |
|---|---|---|---|---|
| charge | 76 | 0.9079 | 1.0 | 1.0 |
| person | 68 | 0.7647 | 0.9412 | 1.0 |
| out_of_scope | 68 | 0.4412 | 1.0 | 1.0 |
| missing | 68 | 0.0 | 0.0 | 0.9265 |

- **The gain is concentrated in one intent.** `missing` (vague messages that need a clarifying question) is 0 of 68 for the baseline and for v1. v2's examples cover it and reach 0.9265 [0.8088, 1.0]. Most of the v1 to v2 difference is this single class, and v2's remaining errors are all in it: 5 of 68 `missing` cases.
- **Failures counted, not hidden:** v2 has 5 wrong cases out of 280 (1.8%), all in `missing`. v1 has 72 wrong, v2 fixes 67 and breaks none. The baseline has 129 wrong. No router version had JSON failures or an unavailable model (`json_failures`, `unavailable`).
- **Known open gap:** greetings and similar openers, planned in [router v3](../../team/router-v3-plan.md). The sealed set does not measure it, which is why v8 exists.

## 4. Variability and robustness (REQ-0022)

- **Stability:** v2 was run three times on 25 bases (100 cases). Agreement is 0.9933 (`versions.router_v2.stability`). Baseline and v1 have no repeated runs; the baseline is deterministic and v1 has no stability measurement. Stability is reported, not an acceptance rule.
- **Noisy twins (n = 50, descriptive):** no case changed outcome under noise for any version (`noisy.degradation_vs_twin`: broken 0, fixed 0). With 50 cases this cannot rule out a small effect; it only shows none was observed.
- **Intervals:** wherever the interval is wider than ±10 points the table says "descriptive" and decides nothing ([018](decisions/018-evaluation-acceptance.md#decision) sizing basis). The baseline's overall interval and its per-variant intervals carry that label.

## 5. Breakdown by language and country (REQ-0024)

`versions.router_v2.breakdown.by_variant` (n = 70 each):

| Variant | Accuracy | 95% interval | Net loss in shared bases |
|---|---|---|---|
| es-MX | 0.9857 | [0.9571, 1.0] | 0 |
| es-AR | 0.9857 | [0.9571, 1.0] | 0 |
| pt-BR | 0.9857 | [0.9571, 1.0] | 0 |
| es-CO | 0.9714 | [0.9286, 1.0] | 1 (`ho-b34`) |

v1 scores 0.7429 on every variant. The baseline spreads 0.5286 to 0.5714 across variants, descriptive only. The one gap in v2 is one base in es-CO, 1 of 70 against a limit of 4 (D6).

Not broken down: system outcomes by customer **segment**. The cases are written text with no customer record, so a segment cut of these results would be invented. The [segment breakdown report](../reports/req_0024_segment_breakdown_report.md) gives the dataset side: transaction volume and dispute eligibility per segment (eligibility 8.42% to 8.50% across Basic, Plus, Premium and Student, n = 4,425,008 transactions). It describes the data, not how the system answers each segment, so the brief's comparison of service outcomes by segment is still missing.

## 6. Outcome metrics of the system replay (REQ-0055)

Replay of the loop with mock Gold, `system.<version>`. The denominator is stated per row.

| Metric | baseline | router_v1 | router_v2 | Denominator |
|---|---|---|---|---|
| Unsafe outcomes | 0 | 0 | 0 | 105 / 75 / 75 |
| Containment (no transfer) | 0.72 (54) | 0.68 (51) | 0.60 (45) | 75 attempted |
| Missed transfers | 45 | 6 | 0 | cases that needed a human |
| Unnecessary transfers | 8 | 2 | 2 | transfers made |
| Safe automated resolution | 0 of 75 | 0 of 75 | 0 of 75 | 75 attempted |
| Cost per attempted case (USD) | 0 | 0.000049 | 0.000134 | 75 |
| Cost per successful resolution | not defined | not defined | not defined | no resolutions |
| Latency p50 / p95 (ms) | 0.71 / 0.93 | 971 / 3829 | 938 / 2721 | 105 / 75 / 75 |

How to read it:

- **Unsafe outcomes: 0/75 per router version, 0/105 for the baseline.** By the rule of three, the true rate is at most 3/75 = 4% with 95% confidence. Zero on a small sample is not zero risk. Every unsafe outcome would be listed in `unsafe_outcomes.cases`; the lists are empty.
- **The baseline "wins" containment and loses safety.** Its higher containment (0.72) comes from not escalating: 45 missed transfers, the cases that needed a person and did not get one. v2 contains less (0.60) and misses none. Containment is read with missed transfers, never alone ([metrics](metrics.md#1-outcome)).
- **Safe automated resolution is 0 of 75 for every version.** This is a property of the replay, not a result: no single-turn case reaches a confirmed dispute, so no case can count as resolved. The run therefore **does not show** a safe-resolution rate and cost per resolution is "not defined". The end-to-end claim rests on the live checks in [delivery](../requirements/delivery.md#req-0035) and the transcript replay, not on these numbers. No ROI figure is derived from this table (REQ-0057 stays a labelled projection).
- **Latency caveat:** component latency comes from the recorded live calls (p50 about 1.1 s, p95 about 4.4 s). System latency for the router versions also includes live model calls, although the run's note says replay time ([018](decisions/018-evaluation-acceptance.md#result)). The baseline's sub-millisecond figures are code only.

### Resolution run over the mock store (REQ-0055)

The final measurement is [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json): the same committed 56-case set in 14 situations, paired baseline and `router_v2`, replayed on the final loop (`measured_commit` is recorded in the summary) after the chat-loop change. [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json), measured before that change, stays beside it as the reference. Both runs verify offline (`python3 -m eval.run verify 2024Q4-resolution-v2`, same for v1, with the 016 model pair in the environment); both replays are simulations over a mock store, not field rates (decision 022).

| Metric | v1 baseline | v1 router_v2 | v2 baseline | v2 router_v2 | Denominator |
|---|---|---|---|---|---|
| Safe automated resolution | 16 (0.2857) | 16 (0.2857) | 16 (0.2857) | 16 (0.2857) | 56 attempted |
| Unsafe outcomes | 0 | 0 | 0 | 0 | 56 |
| Missed transfers | 0 | 0 | 0 | 0 | 28 must-hand-off |
| Unnecessary transfers | 0 | 0 | 0 | 0 | — |
| Containment | 0.5 | 0.5 | 0.5 | 0.5 | 56 attempted |
| Cost per attempted case (USD) | 0 | 0.00016 | 0 | 0.00016 | 56 |
| Cost per successful resolution (USD) | 0 | 0.000561 | 0 | 0.000561 | 16 resolutions |
| Latency p50 / p95 (ms) | 0.46 / 0.58 | 0.46 / 0.63 | 0.65 / 1.18 | 0.64 / 1.09 | replay |

- The chat-loop change (response language from the interface) moved **no outcome on this set**: v2 reproduces v1's counts case for case, which is why `verify` on v1 also matches on the final loop. The re-measurement exists because the loop moved, and because v2 carries the breakdown below.
- The paired resolution difference is **0 of 56** in both runs (interval [0, 0], not above zero): by rule R3 of [022](decisions/022-resolution-acceptance.md) `router_v2` does **not** resolve more than the baseline. R1 (safe), R2 (no missed transfers) and R4 (router unsafe) pass in both runs.
- Both versions resolve the same 16 cases (the four eligible situations in four variants each) and refuse or hand off the rest. Cost per resolution is USD 0.000561 for `router_v2` from the 8 recorded live calls (recorded under the USD 0.45 cap in v1; the v2 replay made no live call).
- No ROI figure is derived from this replay beyond the rate and the costs cited above; the projection is a separate labelled page ([ROI](roi.md)).
- `Pending` is not covered (no `Pending` row in the mock store); the set covers `Refunded` as `status.reversed`.

### Breakdown by variant and country (REQ-0024, simulated)

`system.<version>.by_variant` / `by_country` of the v2 run. Group counts add up to the 56 totals; the interval resamples the 14 situations.

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

Every group interval is wider than ±10 points, so **every group is descriptive**: no disparity between variants or countries is claimed from this set, and none is excluded. Baseline and `router_v2` share the same per-group figures because they resolve the same cases.

**Segment is declared, not invented:** these system outcomes are **not** broken down by customer segment. The resolution cases carry no customer record, so there is no segment to group by; the [segment breakdown report](../reports/req_0024_segment_breakdown_report.md) covers the dataset side only and is cited as dataset context, not as a measurement of how the system answers each segment.

### Country monitoring (REQ-0050)

The v2 replay's turn log, aggregated per country and language by `sentinel-ai-core/eval/monitor.py` and frozen in [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json). The workload is stated there: 256 chat turns in 888 records, the full replay (baseline and `router_v2`), **labelled simulated** — it is not field behaviour.

| Country | Language | Turns | Latency p50 / p95 (ms) | Escalations | Handoffs | Fallback turns | Cost (USD) |
|---|---|---|---|---|---|---|---|
| AR | es-419 | 28 | 0.79 / 1.29 | 8 | 8 | 0 | 0.001916 |
| AR | pt-BR | 28 | 0.91 / 1.41 | 8 | 8 | 0 | 0 |
| CO | es-419 | 28 | 0.79 / 1.28 | 8 | 8 | 0 | 0.001916 |
| CO | pt-BR | 28 | 0.84 / 1.41 | 8 | 8 | 0 | 0 |
| MX | es-419 | 72 | 0.78 / 1.31 | 12 | 12 | 0 | 0.00514 |
| MX | pt-BR | 72 | 0.82 / 1.43 | 12 | 12 | 0 | 0 |

- No failed or timed-out step, and no fallback turn, in any group of this workload.
- Cost sits under es-419 only because understand records carry the session language **before** detection; the model was called for pt-BR turns too, on the strong route (the same 8 recordings).
- Aggregates only: the monitoring output holds no trace id, session reference or text; an unknown country would be reported apart under `other`.

## 7. Justification of metrics, thresholds and splits (REQ-0017)

### Metrics

| Metric | Why this one |
|---|---|
| Accuracy of the intent label, with a paired net difference | The router has one decision, so accuracy is what the brief's comparison asks. The paired difference (bases fixed minus bases broken) answers REQ-0016 directly: it cannot hide a case the new component breaks. |
| Cluster bootstrap over bases | The 4 variants of a base are not independent. Resampling the 70 bases gives honest intervals; resampling 280 cases would be too narrow. |
| Missed and unnecessary transfers | Cost is asymmetric: a missed transfer leaves a customer who needs a person without one; an unnecessary one costs advisor time. They are reported separately, never as one error rate. |
| Unsafe outcomes with denominator | Top metric of the brief; reported as count over attempts with the rule-of-three bound. |
| Median and p95 latency, cost per case | Averages hide the tail that causes abandonment ([metrics](metrics.md#rules-for-all-metrics)). Cost is total over cases, never mixed with unit costs. |

Accuracy per class (F1) is not the primary metric because the main block is balanced by construction; per-intent accuracy in section 3 serves the same purpose and shows the one class that carries the gain.

### Thresholds

All thresholds were fixed in [018](decisions/018-evaluation-acceptance.md) **before** the run, in cases rather than percentages, so anyone can check them:

| Rule | Threshold | Why this value |
|---|---|---|
| D5 beats baseline | Interval of the paired net difference entirely above zero | A point gain with an interval crossing zero is not evidence. 280 cases detect about 7 points with power 0.8 (McNemar). |
| D6 variants comparable | Net loss against the best variant at most 4 of 70 | The 5-point tolerance of 016 is 3.5 cases of 70, rounded up. |
| D7 safety | 0 unsafe outcomes on 75 attacks | Zero tolerance; the bound of 4% is the honest reading of zero on 75. |
| "Descriptive" label | Interval wider than ±10 points | Such a number decides nothing. |

Result against each rule: D4 router v2, D5 passes (+124, above zero), D6 passes (largest loss 1 of 70), D7 passes (0/75). Detail and fields in [018](decisions/018-evaluation-acceptance.md#result). The choice of model pair was made on development only ([016](decisions/016-router-models.md)); the held-out never informed it.

### Splits and leakage

1. **Development and held-out are disjoint.** Development holds 164 cases (`2024Q4-select-v2`, `split: development`); the held-out holds 405 (`2024Q4-eval-v7`). Variants of one base stay on the same side (split by unit). The 10 old held-out cases moved to development after being measured six times ([018](decisions/018-evaluation-acceptance.md#context)).
2. **Sealed before measuring.** The held-out is sealed by hash (`seal.hash`; `sentinel-ai-core/eval/cases/seal.json`), measured once, and `sentinel-ai-core/eval/measured.json` records that. A second measurement of the same seal is refused by the runner.
3. **Isolated authorship.** The held-out writer could not read the prompt, the development cases, the examples or the decisions on thresholds ([018](decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing)). The v2 examples (8, ids in `examples_v2.ids`) come from development cases only.
4. **Time split applies to the data pipeline, not to the router set.** The router cases are simulation with no timestamps, so a temporal split would be meaningless for them. For the dataset-derived label universe the cut is 2025-07-01, enforced in code, with a leak check of 5611 of 5611 and no shared ids between development and held-out ([REQ-0017](../requirements/data-ml.md#req-0017), `evidence/evaluation/method.md`).

## 8. Limits to state with these numbers (REQ-0013)

- **Model-written cases.** Author and reviewer are Claude models given the same label definitions; no human reviewed the cases and no Portuguese speaker is on the team. A 0.98 accuracy shows agreement with those definitions, **not** field accuracy. A bias shared by author and reviewer would not be caught.
- **Balanced, not real, mix.** Class shares are designed; overall accuracy does not transfer to the real distribution of contacts.
- **Small samples.** 70 cases per variant (about ±7 points at 90% accuracy), 50 noisy twins, 100 cases for stability, 75 attacks. Strict equivalence between variants (about 500 per variant at ±5 points) is not claimed.
- **Safe resolution is measured as a simulation only** (section 6, mock store, 56 cases) and **no segment breakdown of system outcomes** exists (section 5; the cases carry no customer record); the segment report covers the dataset only.
- **Mock Gold.** The replay does not read real Gold ([tasks](../../team/tasks.md) 3 and 4).
- **One model family measured,** one temperature, one seed; no production traffic, no drift.
- **Greeting gap** not covered by the sealed set; planned in router v3.

## 9. Reproduction

```
cd sentinel-ai-core
python3 -m eval.run verify 2024Q4-eval-v7
```

Checked on 2026-10-02 (with `SENTINEL_LLM_CHEAP_MODEL` and `SENTINEL_LLM_STRONG_MODEL` set to the 016 pair): the **component block** (sections 2 to 5) replays identically from the recordings. The **system block** (section 6) does **not** reproduce on that machine: `verify` reports "DIFFERS" and the replayed system metrics differ from the frozen ones (for example containment 1.0 instead of 0.60 for v2, and no cost). [018](decisions/018-evaluation-acceptance.md#result) says only spend and latency differ, so that statement is wrong until the cause is found. Section 6 therefore cites the frozen `summary.json` as is and is not independently reproduced here. The frozen run is never edited; a new measurement is a new folder.

**Cause found (2026-10-02, task 1.1).** Two effects, both in the harness, none in the recorded model answers:

1. **Latency was compared.** At the freeze commit, `_comparable` removed only `spend`, not the wall-clock `latency_ms`. The frozen system latency for the router versions came from the live calls (p50 about 0.97 s); a replay makes no live call (p50 under 1 ms), so `verify` reported DIFFERS even at the freeze commit. Re-running `verify` at `3af2553` (the commit that froze `eval-v7`) shows the system block differs **only** in `latency_ms`. A later commit added `_strip`, which excludes `latency_ms` from the comparison.
2. **The loop moved.** The system block replays the live application loop, not a frozen artifact. Commits after the freeze changed the loop: `a7e9b76` offers on the first out-of-scope turn instead of handing off, `cff4d99` hands off on the third, and `71f6446` answers why follow-ups. The recordings did not change (`git diff 3af2553..HEAD -- app/ai/fixtures` is empty), so the frozen outcomes stay fixed while containment, missed transfers and cost move. The component block is a pure function of the cases and the recordings, which is why it still reproduces.

Consequence: a frozen run's **system** block is only reproducible while the loop stays put. The `resolution-eval` run is frozen with the loop at a recorded commit (task 4.3) so its replay is reproducible, and a later loop change means a new run, not an edit.
