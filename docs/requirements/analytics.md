# Requirements: Analytics

Analysis that justifies the flow and the metrics that prove the system works. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0014](#req-0014) | Data-backed problem | P0 | analysis | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0022](#req-0022) | Metrics with n, mix and variability | P0 | analysis | [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055) | In progress |
| [REQ-0024](#req-0024) | Breakdown by language, country and segment | P1 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022) | In progress |
| [REQ-0050](#req-0050) | Monitoring by country | P1 | analysis | [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025) | Pending |
| [REQ-0053](#req-0053) | Sizing and its limits | P0 | analysis | [REQ-0014](#req-0014) | In progress |
| [REQ-0055](#req-0055) | Mandatory outcome metrics | P0 | analysis, ml | [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025) | In progress |
| [REQ-0057](#req-0057) | Business outcomes and ROI | P1 | analysis | [REQ-0055](#req-0055) | In progress |

<a id="req-0014"></a>
### REQ-0014 · Data-backed problem

Use the dataset to show the chosen flow matters: contact reasons, demand, data quality and operational constraints, in a reproducible analysis.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0031](data-ml.md#req-0031). The analysis uses approved, labeled data.

**Evidence:** Proven by: the reproducible [flow measurements](../build/flows/02-flow-measurements.md) and [flow selection](../build/flows/03-flow-selection.md).

<a id="req-0022"></a>
### REQ-0022 · Metrics with n, mix and variability

Every reported metric states how many cases it covers, their mix, the versions used and how much it varies between runs, and failures are included rather than hidden.

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 5; Evaluation evidence

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055). Reports the held-out metrics with n and failures.

**Evidence:** Proven by: n, mix, versions and failures per metric in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

Missing: run-to-run variability, on the final run.

<a id="req-0024"></a>
### REQ-0024 · Breakdown by language, country and segment

Compare outcomes by language, country and authorized customer segment (the `segment` column of `customers`: Premium, Plus, Basic, Student), investigate disparities and state small-sample limits. Offline results, simulations and projections are labeled separately.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022). Breakdown of the reported metrics by language and country.

**Evidence:** Proven by: metrics by locale and country with small-sample limits in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json), labeled as offline simulation.

Missing: the segment breakdown and the disparity analysis.

<a id="req-0050"></a>
### REQ-0050 · Monitoring by country

Monitor latency, failures, escalations and complaints per country.

**Priority:** P1 · **Status:** Pending · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring)

**Depends on:** [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025). Country monitoring reads the logs and the breakdown.

**Evidence:** Missing: the report by country from the logs.

<a id="req-0053"></a>
### REQ-0053 · Sizing and its limits

How many disputes per day appear in the data, what capacity the prototype is designed for, and what changes at real volume (help channel, 9/28).

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Help channel (9/28)

**Depends on:** [REQ-0014](#req-0014). Sizing uses the dispute volumes from the analysis.

**Evidence:** Missing: the sizing section.

<a id="req-0055"></a>
### REQ-0055 · Mandatory outcome metrics

Report the brief's outcome metrics: safe automated resolution (plus the share attempted), containment, escalation quality (missed and unnecessary transfers), unsafe outcomes with counts and denominators, p50/p95 latency, and cost per attempted case and per successful resolution ("not defined" if there are none).

**Priority:** P0 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis, ml

**Source:** Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025). Metrics on the held-out, latency and cost from the logs.

**Evidence:** Proven by: the full set with denominators in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json); the router reports tokens and cost per turn (`tests/test_ai_router.py`).

Missing: the final [metrics](../build/metrics.md) report on the final run.

<a id="req-0057"></a>
### REQ-0057 · Business outcomes and ROI

The intended customer and business outcomes, with cost-per-resolution ROI against the baseline. Projected savings are labeled as projections.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0055](#req-0055). ROI uses cost per resolution.

**Evidence:** Proven by: cost per attempted case and per resolution measured in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json) ("not defined" without resolutions).

Missing: the ROI write-up, labeled as a projection.
