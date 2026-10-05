---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Requirements: Data and ML

This page covers the data preparation, the sources and their freshness. It also covers the learned component, with its labels, splits and tracking. The [requirements index](requirements.md) holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0015](#req-0015) | Repeatable pipeline with contracts | P0 | data | [REQ-0031](#req-0031) | Done |
| [REQ-0016](#req-0016) | Learned component vs baseline | P0 | ml | [REQ-0017](#req-0017), [REQ-0020](#req-0020) | Done |
| [REQ-0017](#req-0017) | Valid labels, no leakage | P0 | ml | [REQ-0015](#req-0015) | Done |
| [REQ-0018](#req-0018) | Real incremental processing | P0 | data | [REQ-0015](#req-0015) | Done |
| [REQ-0019](#req-0019) | Experiment tracking | P1 | ml | [REQ-0016](#req-0016) | Done |
| [REQ-0020](#req-0020) | Same held-out for baseline and system | P0 | ml | [REQ-0017](#req-0017) | Done |
| [REQ-0023](#req-0023) | Validated LLM judge, if used | P2 | ml | [REQ-0016](#req-0016) | Pending |
| [REQ-0031](#req-0031) | Approved data, labeled by origin | P0 | data | — | Done |
| [REQ-0039](#req-0039) | Declare data freshness | P0 | ai, data | [REQ-0015](#req-0015) | Done |
| [REQ-0054](#req-0054) | Justified external data | P1 | data, ml | [REQ-0031](#req-0031) | Done |

<a id="req-0015"></a>
### REQ-0015 · Repeatable pipeline with contracts

Build a data preparation pipeline (Bronze, Silver, Gold) that runs the same way every time. The pipeline enforces column contracts, checks quality and records lineage and freshness. It handles the issues that the dataset declares: about 2% duplicates, 5% nulls and orphaned records.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Dataset summary · Dictionary

**Depends on:** [REQ-0031](#req-0031). The pipeline ingests approved, labeled data.

**Evidence:** Proven by a full run of the pipeline on the whole dataset into `data/gold_bank.duckdb`. The [data quality and medallion audit report](../../sentinel-data-engine/data_quality_report.md) documents the run:

- Null rates: 0.00% across all mandatory fields.
- Bronze to Silver volume drop: about 11.5%. Deduplication, quarantine, orphan filtering and Bronze I/O aggregation explain it.
- 40,515 country-name normalizations.
- 100% referential integrity.
- 373,443 eligible disputes (8.4%).
- A Gold service view with no PII, verified against ADR 023.

The team corrected the `fraud_score` range constraint to 0–100, as the data dictionary says. The correction removed false quarantines. The data-engine test suite verifies it (32 of 32 tests passed when the fix landed; 40 tests pass on 2026-10-05).

<a id="req-0016"></a>
### REQ-0016 · Learned component vs baseline

Evaluate at least one learned component against a simpler baseline on held-out cases. A prompted LLM counts if the team defines, evaluates and justifies it (help channel, 9/28). Our component is the prompted router. The baseline uses keywords.

**Priority:** P0 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Help channel (9/28)

**Depends on:** [REQ-0017](#req-0017), [REQ-0020](#req-0020). The comparison needs valid labels and a shared held-out set.

**Evidence:** Proven by [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json). It compares the prompted router (GLM 5.3 Flash, prompt v2) with the keyword baseline on the same 280 sealed held-out cases. The team measured once. The net result is +124 of 280 cases (`component.paired.router_v2_vs_baseline`, interval [0.3286, 0.55]). D5 in [018](../build/decisions/018-evaluation-acceptance.md) judges the result.

The router also reports a confidence for each label. The team calibrated the two cut-offs on the development and validation split. [`evidence/evaluation-runs/2024Q4-calibration-v1/summary.json`](../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) freezes them (`cutoffs.t_act` = 0.86, `cutoffs.t_abstain` = 0.0; validation n = 26, descriptive). The variable `SENTINEL_LLM_CUTOFFS` switches them on. The `eval-v8` measurement uses them through router-v3.

A second learned component is the charge selector. It has exact labels from real transactions. [`charge-ranker/test-v1`](../../evidence/charge-ranker/test-v1/summary.json) compares it with the rules on a later test split. No customer is in both the test split and another split (`configurations.<name>.all.*`, [025](../build/decisions/025-charge-selector.md)). It stays off in the demo, because it fails the serving rule.

The team also trained and froze a stronger opponent: TF-IDF on character n-grams and a logistic regression. It trains on development and the team tunes it on validation. See [`evidence/evaluation-runs/2024Q4-train-v1/summary.json`](../../evidence/evaluation-runs/2024Q4-train-v1/summary.json) (`splits`, `model.regularization_c`, `validation.selected`, `model.sha256`; [007](../build/decisions/007-learned-component.md)). The plan `eval-v8` does the sealed comparison with the router.

Missing: nothing for the brief. The cases are a model-written simulation. [018](../build/decisions/018-evaluation-acceptance.md) states this limit.

<a id="req-0017"></a>
### REQ-0017 · Valid labels, no leakage

The labels must be trustworthy. The evaluation must not see information from the future or from training. Justify the metrics, the thresholds and the splits.

**Priority:** P0 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12

**Depends on:** [REQ-0015](#req-0015). The labels come from the pipeline output.

**Evidence:** Proven by:

- The 2024Q4 window with the held-out cut 2025-07-01. The code enforces the cut (`evidence/evaluation/method.md`).
- The leak check 5611/5611 in `evidence/evaluation/2024Q4-v1/summary.json`.
- Development and held-out splits with no shared ids in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).
- Splits of the charge selector by customer and by date. [`charge-ranker/data-v1`](../../evidence/charge-ranker/data-v1/summary.json) holds the frozen counts and hashes (`checks.customers_in_two_splits` = 0, `checks.test_only_families_outside_test` = 0).

The labels are exact. Each description comes from one known transaction.

The written justification of the metrics, thresholds and splits is section 7 of the [metrics report](../build/metrics-report.md#7-justification-of-metrics-thresholds-and-splits-req-0017).

The team sealed the router held-out set by hash before it measured. The team measured once (`sentinel-ai-core/eval/cases/seal.json`, `eval/measured.json`). The earlier 10 held-out cases moved to development ([018](../build/decisions/018-evaluation-acceptance.md)). The resolution set resamples its 14 base situations for each interval ([`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json)). For this reason, the four variants of one situation never count as four independent cases.

Stated limit, not missing work: the router cases are a model-written simulation. No native speaker reviewed them ([018](../build/decisions/018-evaluation-acceptance.md)). The label universe is frozen data evidence. A field check of the labels stays future work.

<a id="req-0018"></a>
### REQ-0018 · Real incremental processing

Show that the pipeline updates correctly when data arrives late, arrives twice or changes schema. The data is static. The brief accepts a clearly labeled test fixture as proof.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Architecture freedom · Dataset summary

**Depends on:** [REQ-0015](#req-0015). Incremental processing extends the pipeline.

**Evidence:** Proven by a labeled two-batch fixture. It covers a late arrival, an exact duplicate and a new column. The test checks Silver and Gold after each batch (`sentinel-data-engine/tests/test_incremental_fixture.py`).

<a id="req-0019"></a>
### REQ-0019 · Experiment tracking

Record the model, the prompt version, the parameters and the metrics that produced each result. Then anyone can trace and repeat a run.

**Priority:** P1 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml

**Source:** Kickoff p. 20

**Depends on:** [REQ-0016](#req-0016). The page tracks the versions of the learned component.

**Evidence:** Proven by:

- The router `describe` output, with tokens and cost, on the `understand` record (`tests/test_ai_router.py`).
- The model, route and prompt provenance and the label provenance of each run, in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).
- The served app. It records the model, the route and the prompt version of each turn. The route is `fallback` when the baseline answered (`tests/test_model_serving.py`).
- One write-once folder for each evaluation run ([013](../build/decisions/013-experiment-tracking.md)). The folder names the models, the route, the prompt version, the prices and the spend:
  - [`2024Q4-select-v2`](../../evidence/evaluation-runs/2024Q4-select-v2/summary.json) (`candidates.<model>`),
  - [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.versions.<version>.models`, `prices`, `spend`),
  - [`2024Q4-calibration-v1`](../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) (`cutoffs`).
- The training run [`2024Q4-train-v1`](../../evidence/evaluation-runs/2024Q4-train-v1/summary.json). It records the split ids, the parameter, the scikit-learn version and the model hash (`model`, `splits`). The command `eval.run verify` trains again and compares ([013](../build/decisions/013-experiment-tracking.md)).
- The remote checks of the public link on 2026-10-02 and 2026-10-03 ([REQ-0035](delivery.md#req-0035)).
- The [evidence index](../../evidence/README.md#evaluation-runs). It lists each run and its status.

The frozen runs are the tracking record. The team uses no extra tool ([013](../build/decisions/013-experiment-tracking.md)).

Missing: the parameters of the live models. The run that measures [016](../build/decisions/016-router-models.md) records them.

<a id="req-0020"></a>
### REQ-0020 · Same held-out for baseline and system

Compare the baseline and the system on exactly the same held-out cases. Make that set resemble the real distribution.

**Priority:** P0 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: Evaluation evidence · Kickoff p. 12

**Depends on:** [REQ-0017](#req-0017). The held-out set uses valid labels.

**Evidence:** Proven by [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.case_ids`). It runs the baseline, router v1 and router v2 on the same 280 sealed cases. The team measured once. [018](../build/decisions/018-evaluation-acceptance.md) declares the case mix and its model-written origin.

Missing: nothing for the brief. The mix is a designed simulation (70 bases by 4 variants, at least 25 per intent). [018](../build/decisions/018-evaluation-acceptance.md) states this as a limit.

<a id="req-0023"></a>
### REQ-0023 · Validated LLM judge, if used

This applies only if a model judges the answers. The team must document its rubric. The team must check the rubric on a sample against human judgments or deterministic judgments.

**Priority:** P2 · **Status:** Pending · **Criterion:** Machine Learning · **Area:** ml · **Flow:** If applicable

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0016](#req-0016). This applies only to an LLM component that a model judges.

**Evidence:** Not used so far. Deterministic checks judge the answers. Close the requirement as not applicable if that stays true.

<a id="req-0031"></a>
### REQ-0031 · Approved data, labeled by origin

Use only data that the organizers approved. Label each input as real, de-identified, synthetic or team-generated. The organizer dataset is fully synthetic. The dataset summary says: "no real customer information is included".

**Priority:** P0 · **Status:** Done · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Data and execution boundaries

**Evidence:** Proven by:

- The [source inventory](../data_inventory.md). It labels each input by origin (organizer synthetic dataset, team-written fixtures and evaluation cases). It lists no external data and no real customer data.
- The [what is real](../architecture/what-is-real.md) page. It labels each component, data source and number as real, mock, synthetic, team-generated, simulation or projection.
- The [evidence index](../../evidence/README.md). It labels each run the same way.

<a id="req-0039"></a>
### REQ-0039 · Declare data freshness

Each answer about data says how current the data is ("updated through ..."). The answer never claims anything newer. The dataset ends on 2026-06-17.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / Data Engineering · **Area:** ai, data

**Source:** Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) · Dataset summary (data ends 2026-06-17)

**Depends on:** [REQ-0015](#req-0015). The freshness comes from the as-of date of the pipeline.

**Evidence:** Proven by `as_of` on the listing and `referenceDate` on each confirmation. Both come from one configurable reference date (`test_screen_and_engine_share_the_default_reference_date`, `tests/test_contract.py`).

<a id="req-0054"></a>
### REQ-0054 · Justified external data

The team may use external data only with a justification. The justification gives the source, the license and the reason for the need. The data has no personal data. The team labels it as external.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Engineering · **Area:** data, ml

**Source:** Help channel (9/28)

**Depends on:** [REQ-0031](#req-0031). It uses the same source inventory.

**Evidence:** Proven by the fact that the system uses no external data. The [source inventory](../data_inventory.md) declares this (section 3.3).
