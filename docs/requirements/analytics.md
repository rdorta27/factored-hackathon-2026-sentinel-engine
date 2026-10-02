# Requirements: Analytics

Analysis that justifies the flow and the metrics that prove the system works. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0014](#req-0014) | Data-backed problem | P0 | analysis | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0022](#req-0022) | Metrics with n, mix and variability | P0 | analysis | [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055) | Done |
| [REQ-0024](#req-0024) | Breakdown by language, country and segment | P1 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022) | In progress |
| [REQ-0050](#req-0050) | Monitoring by country | P1 | analysis | [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025) | In progress |
| [REQ-0053](#req-0053) | Sizing and its limits | P0 | analysis | [REQ-0014](#req-0014) | Done |
| [REQ-0055](#req-0055) | Mandatory outcome metrics | P0 | analysis, ml | [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025) | Done |
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

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 5; Evaluation evidence

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055). Reports the held-out metrics with n and failures.

**Evidence:** Proven by: n, case mix, model and prompt versions, failures, base-level 95% intervals and stability over 3 recorded repetitions on 100 cases in [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.versions.router_v2.stability`).

Missing: nothing for the router component.

<a id="req-0024"></a>
### REQ-0024 · Breakdown by language, country and segment

Compare outcomes by language, country and authorized customer segment (the `segment` column of `customers`: Premium, Plus, Basic, Student), investigate disparities and state small-sample limits. Offline results, simulations and projections are labeled separately.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022). Breakdown of the reported metrics by language and country.

**Evidence:** Proven by: accuracy per variant (es-MX, es-CO, es-AR, pt-BR) and per intent with intervals and a paired per-variant loss in [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.versions.<version>.breakdown`, `variant_losses`). Dataset context: the [segment breakdown report](../reports/req_0024_segment_breakdown_report.md) gives transaction volume and dispute eligibility per segment.

Missing: system outcomes (resolution, transfers, unsafe outcomes, latency, cost) per language and country, planned in `evaluation-final`; a segment cut of system outcomes is not possible on cases without a customer record and is declared.

<a id="req-0050"></a>
### REQ-0050 · Monitoring by country

Monitor latency, failures, escalations and complaints per country.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring)

**Depends on:** [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025). Country monitoring reads the logs and the breakdown.

**Evidence:** Dataset context: the [country log analytics report](../reports/req_0050_country_logs_report.md) analyses the bank's digital events, call-center interactions and surveys per country. The app's turn records carry `country` and `language` on every step (`app/observability/`).

Missing: monitoring of the app itself (latency, failures, escalations per country) from its turn log, planned in `evaluation-final`.

<a id="req-0053"></a>
### REQ-0053 · Sizing and its limits

How many disputes per day appear in the data, what capacity the prototype is designed for, and what changes at real volume (help channel, 9/28).

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Help channel (9/28)

**Depends on:** [REQ-0014](#req-0014). Sizing uses the dispute volumes from the analysis.

**Evidence:** Proven by: the [sizing and capacity specification](../sizing_capacity.md): dispute volume and daily load from the data, prototype capacity (DuckDB, SQLite, one instance) and what changes at real volume.

<a id="req-0055"></a>
### REQ-0055 · Mandatory outcome metrics

Report the brief's outcome metrics: safe automated resolution (plus the share attempted), containment, escalation quality (missed and unnecessary transfers), unsafe outcomes with counts and denominators, p50/p95 latency, and cost per attempted case and per successful resolution ("not defined" if there are none).

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis, ml

**Source:** Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025). Metrics on the held-out, latency and cost from the logs.

**Evidence:** Proven by: every mandatory metric with its denominator in the [metrics report](../build/metrics-report.md) (section 6): intent and system metrics on [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json), and safe automated resolution on [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json): 16 of 56 cases in 14 situations for the baseline and router_v2, 0 unsafe outcomes, 0 missed transfers, cost per resolution USD 0.000561 for router_v2; the resolution run verifies offline.

Missing: nothing for the brief. Stated limits: a simulation over a mock store, not a field rate; the pending status is not covered; the system block of `eval-v7` does not replay offline (report section 9). The final re-measure after `chat-loop`, with the breakdown, is `evaluation-final`.

<a id="req-0057"></a>
### REQ-0057 · Business outcomes and ROI

The intended customer and business outcomes, with cost-per-resolution ROI against the baseline. Projected savings are labeled as projections.

**Priority:** P1 · **Status:** In progress · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0055](#req-0055). ROI uses cost per resolution.

**Evidence:** Proven by: cost per attempted case and per resolution measured in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json) ("not defined" without resolutions) and in [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) (USD 0.000561 per resolution for `router_v2` on the mock store; the baseline is free code).

Missing: the ROI write-up, labeled as a projection, and any field resolution rate.
