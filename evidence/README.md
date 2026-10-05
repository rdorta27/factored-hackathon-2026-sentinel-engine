---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Evidence

This folder holds the frozen measurement runs. The documentation cites these runs. Each run is one folder with a `summary.json`. Cite a field of `summary.json`. Do not copy a number by hand.

**Rules**

- A run is write-once. Do not edit a committed run. A new measurement goes in a new folder.
- A run holds aggregates only. It holds no dataset rows, customer ids or bucket names.
- Raw data stays outside git (`data/`, `sentinel-data-engine/data/`).

**Data type of each run.** Every row below has one of these labels. The [what is real](../docs/architecture/what-is-real.md) page explains them.

| Label | Meaning |
|---|---|
| **Dataset** | Aggregates of the hackathon dataset. The dataset is synthetic. The organizers supplied it. |
| **Simulation** | Team-written or model-written conversations. They are not dataset rows and not production traffic. |
| **Mock store** | The run reads the labelled Gold mock (`app/tools/gold.py`), not real Gold. |
| **Replay** | The run replays recorded model answers. It makes no live model call. |
| **Test suite** | The pytest outcomes of the adversarial suite. |
| **Projection** | A calculation from assumed values. It is not a measurement. |

## Which run to cite

| Question | Current run | Field to cite |
|---|---|---|
| Which flow did we choose, and why? | [`flows/2024Q4-v3`](flows/2024Q4-v3/README.md) | `disputes.*`, `accounts.*` |
| How big is the problem behind the flow? | [`problem/dev-v1`](problem/dev-v1/README.md) | `reasons.*`, `demand.*`, `hours.*`, `missing.*` |
| Does the router beat the baseline? | [`evaluation-runs/2024Q4-eval-v7`](evaluation-runs/2024Q4-eval-v7/summary.json) | `component.paired.*`, `component.versions.<version>.breakdown.*` |
| How many cases does the system resolve safely? | [`evaluation-runs/2024Q4-resolution-v2`](evaluation-runs/2024Q4-resolution-v2/summary.json) | `system.<version>.*` |
| What are the confidence cut-offs? | [`evaluation-runs/2024Q4-calibration-v1`](evaluation-runs/2024Q4-calibration-v1/summary.json) | `cutoffs.t_act`, `cutoffs.t_abstain` |
| Does the system resist attacks? | [`adversarial/20261005T014816Z`](adversarial/20261005T014816Z/summary.json) | `totals.unsafe_outcome_rate`, `categories.*` |
| What does monitoring by country show? | [`monitoring/2024Q4-resolution-v2-replay`](monitoring/2024Q4-resolution-v2-replay/summary.json) | `groups.<country>.<language>.*` |
| What does the ROI projection use? | [`roi/2023-2026-callcenter-v1`](roi/2023-2026-callcenter-v1/summary.json) | `transactional_calls.*` |
| Does the learned charge selector beat the rules? | [`charge-ranker/test-v1`](charge-ranker/test-v1/summary.json) | `configurations.<name>.all.*` |
| Can the data support a charge investigation? | [`customer-360/dev-v1`](customer-360/dev-v1/README.md) and [`customer-360/dev-signals-v1`](customer-360/dev-signals-v1/README.md) | `balance.safe_to_show`, `complaints.charge_linkable`, `investigation.has_signal` |

## Flows

Why the team chose transaction disputes. Script: `measure_flow.py`. Data type: **Dataset**, window 2024Q4, held-out cut 2025-07-01.

| Run | Status | What it adds | Requirements |
|---|---|---|---|
| [`flows/`](flows/README.md) (root) | Superseded | First run: volume, linkage and labels for four flows | REQ-0014 |
| [`flows/2024Q4-v2`](flows/2024Q4-v2/README.md) | Superseded | Regulator share, `was_escalated` on calls, fill audit, `reason_category` finding | REQ-0014, REQ-0017 |
| [`flows/2024Q4-v3`](flows/2024Q4-v3/README.md) | **Current** | Univariate learnability audit for the four targets | REQ-0014, REQ-0016, REQ-0017 |

The raw data for these runs is not in the repository. `verify` needs the data at `evidence/flows/data/`.

## Problem

The measured problem behind the chosen flow. Script: `measure_problem.py`. Data type: **Dataset**, window the development zone (2023-06-17 to 2025-07-01), held-out cut 2025-07-01.

| Run | Status | What it holds | Requirements |
|---|---|---|---|
| [`problem/dev-v1`](problem/dev-v1/README.md) | **Current** | First-contact resolution by reason, calls a day by workflow (mean, busy day, highest day), agent hours a month and missing values | REQ-0014, REQ-0053 |

The reason-to-workflow mapping is in the run README and was committed before the first number. The raw data is not in the repository; `verify` needs the raw call files (see the run `MANIFEST.md`).

## Charge selector

The learned charge selector ([025](../docs/build/decisions/025-charge-selector.md)). Scripts: `sentinel-ai-core/eval/build_charge_splits.py`, `train_charge_ranker.py`, `eval_charge_ranker.py`. Data type: **Simulation**. The transactions are real Gold rows. The descriptions are team-generated. The runs need the local Gold file.

| Run | Status | What it holds | Requirements |
|---|---|---|---|
| [`charge-ranker/data-v1`](charge-ranker/data-v1/README.md) | **Current** | Frozen splits: counts, hashes, seed, families | REQ-0017 |
| [`charge-ranker/train-v1`](charge-ranker/train-v1/README.md) | **Current** | The weights file and its hash, the threshold, the validation result | REQ-0016, REQ-0017, REQ-0019 |
| [`charge-ranker/test-v1`](charge-ranker/test-v1/README.md) | **Current** | Four configurations on the test split, measured once | REQ-0016, REQ-0017, REQ-0020 |

## Evaluation inputs

The label universe, the case mix and the reference thresholds that the evaluation runner reads. Script: `evaluation/eval_measure.py`. Data type: **Dataset**.

| Run | Status | What it holds | Requirements |
|---|---|---|---|
| [`evaluation/2024Q4-v1`](evaluation/2024Q4-v1/README.md) | Superseded | Label universe (10 claim combinations), case mix, intent mix | REQ-0017 |
| [`evaluation/2024Q4-v2`](evaluation/2024Q4-v2/README.md) | **Current** | Adds `account_thresholds`: the p95 fraud and amount values per country and currency ([010](../docs/build/decisions/010-fraud-handoff-rule.md), [011](../docs/build/decisions/011-high-amount-threshold.md)) | REQ-0017, REQ-0006 |

Method and cut: [`evaluation/method.md`](evaluation/method.md).

## Evaluation runs

The runs of the evaluation runner (`sentinel-ai-core/eval/run.py`). Data type: **Simulation**. A run that uses Gold uses the **Mock store**. Each folder has `summary.json` and a generated `report.md`.

Verify a run from `sentinel-ai-core/`. Set the two model names of [016](../docs/build/decisions/016-router-models.md) first. The check makes no live call:

```bash
SENTINEL_LLM_CHEAP_MODEL=accounts/fireworks/models/glm-5p3-flash \
SENTINEL_LLM_STRONG_MODEL=accounts/fireworks/models/glm-5p3-flash \
python3 -m eval.run verify <run-id>
```

| Run | Kind | Status | What it measures | `verify` on 2026-10-05 | Requirements |
|---|---|---|---|---|---|
| `2024Q4-eval-v1` to `2024Q4-eval-v6` | development | Superseded | Runner development. The router used baseline-mirrored fixtures, so the difference is zero by construction. | not checked (`eval-v6` was refused: the case set differs from the one measured) | REQ-0016 |
| [`2024Q4-select-v1`](evaluation-runs/2024Q4-select-v1/summary.json), [`2024Q4-select-v2`](evaluation-runs/2024Q4-select-v2/summary.json) | selection | Current (v2) | Model selection on the development split only ([016](../docs/build/decisions/016-router-models.md)) | refused: the case set differs from the one measured | REQ-0016, REQ-0020 |
| [`2024Q4-eval-v7`](evaluation-runs/2024Q4-eval-v7/summary.json) | held-out | **Current** | Sealed held-out: 405 cases, baseline against router v1 and v2, attacks, noisy twins, system replay | DIFFERS: the component block matches; the system block moved with the loop ([metrics report §9](../docs/build/metrics-report.md#9-reproduction)) | REQ-0016, REQ-0017, REQ-0020, REQ-0022, REQ-0024 |
| [`2024Q4-resolution-v1`](evaluation-runs/2024Q4-resolution-v1/summary.json) | resolution | Superseded | First multi-turn run that can resolve a case: 56 cases in 14 situations ([022](../docs/build/decisions/022-resolution-acceptance.md)) | matches | REQ-0055 |
| [`2024Q4-resolution-v2`](evaluation-runs/2024Q4-resolution-v2/summary.json) | resolution | **Current** | The same set after the chat-loop change, with breakdown by variant and country | matches | REQ-0055, REQ-0024 |
| [`2024Q4-calibration-v1`](evaluation-runs/2024Q4-calibration-v1/summary.json) | calibration | **Current** | Confidence cut-offs on the validation split (n = 26, descriptive) | DIFFERS: the development cases changed on 2026-10-04 (`a17ed3a`), after the run | REQ-0002, REQ-0016 |
| [`2024Q4-select-v3`](evaluation-runs/2024Q4-select-v3/summary.json), [`2024Q4-select-v3c`](evaluation-runs/2024Q4-select-v3c/summary.json) | selection | Superseded | Prompt v3 on development: 8 examples, then the refined prompt. Kept for the iteration history. | refused: the case set differs from the one measured | REQ-0016, REQ-0020 |
| [`2024Q4-select-v3d`](evaluation-runs/2024Q4-select-v3d/summary.json) | selection | **Current (v3)** | Prompt v3 on development (198 cases, 32-example matrix): kind 0.9899, subtype 1.0, 94 drafts with 0 rejected. Offline replay of v3c with the kind-key confidence fix. | refused: the case set differs from the one measured | REQ-0016, REQ-0020 |
| [`2024Q4-calibration-v3`](evaluation-runs/2024Q4-calibration-v3/summary.json) | calibration | **Current (v3)** | v3 cut-offs on the validation split by the 018 rule: `t_act` 1.0, `t_abstain` 0.0 (n = 26, descriptive) | DIFFERS: the development cases changed on 2026-10-04 (`a17ed3a`), after the run | REQ-0002, REQ-0016 |
| [`2024Q4-train-v1`](evaluation-runs/2024Q4-train-v1/summary.json) | training | **Current** | The trained baseline: TF-IDF on character n-grams and a logistic regression. It trains on the development split. It tunes C on the validation split (`validation.by_c`, descriptive). The run holds the split ids, the model file `model.json` and its hash (`model.sha256`). It reads no held-out case. | matches (`python3 -m eval.run verify 2024Q4-train-v1`, scikit-learn 1.9.1 only) | REQ-0016, REQ-0019 |

On 2026-10-05, `verify` matches for `resolution-v1`, `resolution-v2` and `train-v1` only. `eval-v7` and both calibration runs differ from their frozen summary. The selection runs and `eval-v6` are refused, because the case set is not the one that the run measured. A frozen run is never edited. The cause of each difference is not yet confirmed.

## Adversarial

The adversarial suite writes these runs (`SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q`). Data type: **Test suite**. The counts come from the real pytest outcomes. Requirements: REQ-0021, REQ-0007, REQ-0047.

| Run | Status | Attempted | Unsafe | No defense yet |
|---|---|---|---|---|
| [`20261005T014816Z`](adversarial/20261005T014816Z/summary.json) | **Current** | 42 | 0/42 | 0 |
| [`20261004T195343Z`](adversarial/20261004T195343Z/summary.json) | Superseded | 42 | 0/42 | 0 |
| [`20261002T222323Z`](adversarial/20261002T222323Z/summary.json) | Superseded | 42 | 0/42 | 0 |
| `20261002T195516Z` | Superseded | 42 | 0/42 | 3 |
| `20261002T120107Z`, `20261001T222341Z` | Superseded | 36 | 0/36 | 3 |
| `20261001T215949Z`, `20261001T130342Z` | Superseded | 36 | 0/36 | 4 |
| `20261001T122759Z` | Superseded | 34 | 0/34 | 4 |
| `20261001T114008Z`, `20260930T214744Z` | Superseded | 29 | 0/29 | 4 |

Source of each number: `totals.attempted`, `totals.unsafe_outcome_rate`, `totals.no_defense_yet`. In the current run, 3 injection attempts pass only because the keyword model answers them (`categories.A_prompt_injection.passes_on_mock`). The attack block of `eval-v7` tests attacks against the live model.

## Monitoring

| Run | Status | Data type | What it shows | Requirements |
|---|---|---|---|---|
| [`monitoring/2024Q4-resolution-v2-replay`](monitoring/2024Q4-resolution-v2-replay/summary.json) | **Current** | Simulation, Replay | Turn records by country and language over the resolution replay: 256 turns (`workload.*`). No field log exists. | REQ-0050, REQ-0025 |

The country report is [`docs/reports/req_0050_country_logs_report.md`](../docs/reports/req_0050_country_logs_report.md).

## ROI

| Run | Status | Data type | What it holds | Requirements |
|---|---|---|---|---|
| [`roi/2023-2026-callcenter-v1`](roi/2023-2026-callcenter-v1/report.md) | **Current** | Dataset | Call-center aggregates: transactional calls, handle time, first-contact resolution | REQ-0057 |

This run reads the full date range, also after the held-out cut. It is descriptive and does not select or tune a model. The ROI itself is a **Projection** with an assumed advisor-hour cost ([roi](../docs/build/roi.md)).

## Transcript replays

A 2% replay of the dataset transcripts through the chat. Data type: **Dataset** (development side only). The transcripts are two Spanish templates, not customer language.

| Run | Status | What it shows | Requirements |
|---|---|---|---|
| [`transcript-chats/20261002T144836Z`](transcript-chats/20261002T144836Z/summary.json) | **Current** | 280 of 14,023 development openings: 280 handoffs, 2 distinct prefixes | REQ-0012, REQ-0013 |
| `20261002T143213Z`, `20261002T142823Z`, `20261002T142723Z` | Superseded | Earlier samples of the same replay | REQ-0012 |

## Customer 360

Can the dataset support a charge investigation with products, balances, complaint history or customer signals? Data type: **Dataset**, development zone only (before 2025-07-01).

| Run | Status | Answer | Requirements |
|---|---|---|---|
| [`customer-360/dev-v1`](customer-360/dev-v1/README.md) | **Current** | No. The balance has no usable as-of date (`balance.safe_to_show` = false). Complaints link to the customer only (`complaints.charge_linkable` = false). Blocked or closed products have no transactions. No pre-authorization pairs and no duplicates. | REQ-0013, REQ-0015 |
| [`customer-360/dev-signals-v1`](customer-360/dev-signals-v1/README.md) | **Current** | No. No customer signal predicts `is_fraud` or adds to `fraud_score` (`investigation.has_signal` = false). A score above 30 is always fraud: an artefact of the generator (`investigation.label_is_synthetic_artefact`). | REQ-0013, REQ-0016 |

The [investigation data support](../docs/rationale/investigation-data-support.md) page gives the decision.

## Other evidence outside this folder

| What | Where | Data type |
|---|---|---|
| Data quality of the pipeline | [`sentinel-data-engine/data_quality_report.md`](../sentinel-data-engine/data_quality_report.md) | Dataset |
| Segment breakdown of the dataset | [`docs/reports/req_0024_segment_breakdown_report.md`](../docs/reports/req_0024_segment_breakdown_report.md) | Dataset |
| Live deployment checks | [REQ-0035](../docs/requirements/delivery.md#req-0035) and [`deploy/azure/README.md`](../deploy/azure/README.md) | Live service, Mock store |
| Router recordings | `sentinel-ai-core/app/ai/fixtures/`, `sentinel-ai-core/eval/recordings/` | Replay |
