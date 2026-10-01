# Requirements: Data and ML

Data preparation, sources and freshness, and the learned component with its labels, splits and tracking. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0015](#req-0015) | Repeatable pipeline with contracts | P0 | data | [REQ-0031](#req-0031) | In progress |
| [REQ-0016](#req-0016) | Learned component vs baseline | P0 | ml | [REQ-0017](#req-0017), [REQ-0020](#req-0020) | In progress |
| [REQ-0017](#req-0017) | Valid labels, no leakage | P0 | ml | [REQ-0015](#req-0015) | In progress |
| [REQ-0018](#req-0018) | Real incremental processing | P0 | data | [REQ-0015](#req-0015) | Pending |
| [REQ-0019](#req-0019) | Experiment tracking | P1 | ml | [REQ-0016](#req-0016) | In progress |
| [REQ-0020](#req-0020) | Same held-out for baseline and system | P0 | ml | [REQ-0017](#req-0017) | In progress |
| [REQ-0023](#req-0023) | Validated LLM judge, if used | P2 | ml | [REQ-0016](#req-0016) | Pending |
| [REQ-0031](#req-0031) | Approved data, labeled by origin | P0 | data | — | Pending |
| [REQ-0039](#req-0039) | Declare data freshness | P0 | ai, data | [REQ-0015](#req-0015) | Done |
| [REQ-0054](#req-0054) | Justified external data | P1 | data, ml | [REQ-0031](#req-0031) | Pending |

<a id="req-0015"></a>
### REQ-0015 · Repeatable pipeline with contracts

A data preparation pipeline (Bronze, Silver, Gold) that runs the same way every time, enforces column contracts, checks quality, records lineage and freshness, and handles the dataset's declared issues: about 2% duplicates, 5% nulls and orphaned records.

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Dataset summary · Dictionary

**Depends on:** [REQ-0031](#req-0031). The pipeline ingests approved, labeled data.

**Evidence:** Proven by: pipeline code with tests in `sentinel-data-engine/`.

Missing: an end-to-end run and its quality report.

<a id="req-0016"></a>
### REQ-0016 · Learned component vs baseline

At least one learned component evaluated against a simpler baseline on held-out cases. A prompted LLM counts if it is defined, evaluated and justified (help channel, 9/28). Ours is the prompted router against a keyword baseline.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12 · Help channel (9/28)

**Depends on:** [REQ-0017](#req-0017), [REQ-0020](#req-0020). Comparison needs valid labels and a shared held-out.

**Evidence:** Proven by: router and baseline run on the same held-out cases, plus a system replay, in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: the fixtures mirror the baseline, so the measured difference is zero by construction; a live-model run (decision 10) is needed.

<a id="req-0017"></a>
### REQ-0017 · Valid labels, no leakage

Labels must be trustworthy and the evaluation must not see information from the future or from training. Metrics, thresholds and splits must be justified.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: What your solution should demonstrate 4 · Kickoff p. 12

**Depends on:** [REQ-0015](#req-0015). Labels come from the pipeline output.

**Evidence:** Proven by: 2024Q4 window with the held-out cut 2025-07-01 enforced in code (`evidence/evaluation/method.md`); leak check 5611/5611 in `evidence/evaluation/2024Q4-v1/summary.json`; dev and held-out splits with no shared ids in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: one written justification of metrics, thresholds and splits, confirmed on real Gold.

<a id="req-0018"></a>
### REQ-0018 · Real incremental processing

Show the pipeline updates correctly when data arrives late, is duplicated or changes schema. The data is static, so the brief accepts a clearly labeled test fixture as proof.

**Priority:** P0 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Architecture freedom · Dataset summary

**Depends on:** [REQ-0015](#req-0015). Incremental processing extends the pipeline.

**Evidence:** Missing: the labeled fixture and its test.

<a id="req-0019"></a>
### REQ-0019 · Experiment tracking

Record which model, prompt version, parameters and metrics produced each result, so any run can be traced and repeated.

**Priority:** P1 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Kickoff p. 20

**Depends on:** [REQ-0016](#req-0016). Tracks the learned component's versions.

**Evidence:** Proven by: router `describe` plus tokens and cost on the `understand` record (`tests/test_ai_router.py`); model, route, prompt and label provenance per run in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: the live model's parameters, once decision 10 lands.

<a id="req-0020"></a>
### REQ-0020 · Same held-out for baseline and system

Compare the baseline and the system on exactly the same held-out cases, and make that set resemble the real distribution.

**Priority:** P0 · **Status:** In progress · **Criterion:** Machine Learning · **Area:** ml

**Source:** Problem statement: Evaluation evidence · Kickoff p. 12

**Depends on:** [REQ-0017](#req-0017). Held-out built on valid labels.

**Evidence:** Proven by: the same 35 team-written cases for both models and the loop in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json); held-out measured once.

Missing: a justification that the case mix is realistic, or a declared limitation.

<a id="req-0023"></a>
### REQ-0023 · Validated LLM judge, if used

Only applies if a model judges the answers: its rubric must be documented and checked on a sample against human or deterministic judgments.

**Priority:** P2 · **Status:** Pending · **Criterion:** Machine Learning · **Area:** ml · **Flow:** If applicable

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0016](#req-0016). Only applies to an LLM component being judged.

**Evidence:** Not used so far: answers are judged by deterministic checks. Close as not applicable if that holds.

<a id="req-0031"></a>
### REQ-0031 · Approved data, labeled by origin

Use only organizer-approved data and label every input as real, de-identified, synthetic or team-generated. The organizer's dataset is fully synthetic (dataset summary: "no real customer information is included").

**Priority:** P0 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data

**Source:** Problem statement: Data and execution boundaries

**Evidence:** Missing: the source inventory.

<a id="req-0039"></a>
### REQ-0039 · Declare data freshness

Every answer about data says how current it is ("updated through ...") and never claims anything newer. The dataset ends on 2026-06-17.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / Data Engineering · **Area:** ai, data

**Source:** Own: [conversation](../build/conversation.md#when-data-is-not-up-to-date) · Dataset summary (data ends 2026-06-17)

**Depends on:** [REQ-0015](#req-0015). Freshness comes from the pipeline's as-of date.

**Evidence:** Proven by: `as_of` on the listing and `referenceDate` on every confirmation, from one configurable reference date (`test_screen_and_engine_share_the_default_reference_date`, `tests/test_contract.py`).

<a id="req-0054"></a>
### REQ-0054 · Justified external data

External data is allowed only if justified: source, license, why it is needed, no personal data, and labeled as external.

**Priority:** P1 · **Status:** Pending · **Criterion:** Data Engineering · **Area:** data, ml

**Source:** Help channel (9/28)

**Depends on:** [REQ-0031](#req-0031). Same source inventory.

**Evidence:** Missing: none is used; declare it in the source inventory (REQ-0031).
