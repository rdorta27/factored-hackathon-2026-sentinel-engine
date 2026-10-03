# Requirements: Analytics

Analysis that justifies the flow and the metrics that prove the system works. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0014](#req-0014) | Data-backed problem | P0 | analysis | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0022](#req-0022) | Metrics with n, mix and variability | P0 | analysis | [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055) | Done |
| [REQ-0024](#req-0024) | Breakdown by language, country and segment | P1 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022) | Done |
| [REQ-0050](#req-0050) | Monitoring by country | P1 | analysis | [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025) | Done |
| [REQ-0053](#req-0053) | Sizing and its limits | P0 | analysis | [REQ-0014](#req-0014) | Done |
| [REQ-0055](#req-0055) | Mandatory outcome metrics | P0 | analysis, ml | [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025) | Done |
| [REQ-0057](#req-0057) | Business outcomes and ROI | P1 | analysis | [REQ-0055](#req-0055) | Done |

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

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022). Breakdown of the reported metrics by language and country.

**Evidence:** Proven by: (1) accuracy per variant (es-MX, es-CO, es-AR, pt-BR) and per intent with intervals and a paired per-variant loss in [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.versions.<version>.breakdown`, `variant_losses`); (2) the [segment and multi-currency dispute breakdown report](../reports/req_0024_segment_breakdown_report.md) covering transaction volume, eligibility rate, and monetary exposure by segment (Basic, Plus, Premium, Student) and by country/currency (MXN, COP, ARS, USD), backed by `v_service_dispute_eligible_transactions` in `sentinel-data-engine/data/gold_bank.duckdb`; (3) the system's own outcomes broken down per language variant and per account country with n and situation-level 95% intervals in [`evidence/evaluation-runs/2024Q4-resolution-v2/summary.json`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) (`system.<version>.by_variant`, `by_country`), every group labelled descriptive, reported in the [metrics report](../build/metrics-report.md).

System outcomes are not broken down by customer segment: the resolution cases carry no customer record, so there is no segment to group by; the segment figures in (2) are dataset context, not a measurement of how the system answers each segment.

<a id="req-0050"></a>
### REQ-0050 · Monitoring by country

Monitor latency, failures, escalations and complaints per country.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring)

**Depends on:** [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025). Country monitoring reads the logs and the breakdown.

**Evidence:** Proven by: the [country log analytics report](../reports/req_0050_country_logs_report.md) covering digital event volumes (11.9M across México, Colombia, Argentina), call center interaction counts and sentiment scores by country and channel, and customer satisfaction survey averages — all sourced from `bronze_digital_events`, `silver_call_center_interactions`, and `silver_satisfaction_surveys` in `sentinel-data-engine/data/gold_bank.duckdb`; beside the dataset report, the system's own monitoring: `sentinel-ai-core/eval/monitor.py` aggregates the app turn log per country and language (turns, p50/p95 latency, failed or timed-out steps, escalations, handoffs, fallback turns, cost; aggregates only, write-once), frozen for the simulated replay workload in [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json) (256 turns, 888 records) and reported in the [metrics report](../build/metrics-report.md).

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

**Evidence:** Proven by: the [metrics report](../build/metrics-report.md) on the frozen run [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json), with every mandatory metric and its denominator (section 6); the final resolution run [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) (with [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) beside it) measures safe automated resolution over 56 cases in 14 situations on the final loop (16 of 56 for both versions, 0 unsafe, 0 missed transfers, cost per resolution USD 0.000561 for `router_v2`), carries the per-variant and per-country breakdown with n, situation-level intervals and the descriptive label, and verifies offline; the router reports tokens and cost per turn (`tests/test_ai_router.py`).

Stated limits, not missing work: the resolution rate is a simulation over a mock store, not a field resolution rate; the pending status is not covered (no `Pending` row in the mock store). The system block of `eval-v7` does not replay offline (report section 9); the resolution runs do.

<a id="req-0057"></a>
### REQ-0057 · Business outcomes and ROI

The intended customer and business outcomes, with cost-per-resolution ROI against the baseline. Projected savings are labeled as projections.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0055](#req-0055). ROI uses cost per resolution.

**Evidence:** Proven by, as a projection, never a measured saving: [ROI](../build/roi.md) gives the break-even safe-resolution rate (0.21% to 2.99% over the assumed advisor-hour range of USD 5 to 25 and the estimated infrastructure of USD 20 to 60 a month) with every input labelled by origin, the sensitivity table, and the measured simulated rate beside it (16 of 56 = 0.2857, simulation over the mock store); the call-center aggregates behind it are frozen in [`evidence/roi/2023-2026-callcenter-v1/summary.json`](../../evidence/roi/2023-2026-callcenter-v1/summary.json) (240,056 transactional calls, 3.68-minute mean handle time, 0.9151 first-contact resolution, 0.0993 escalation, aggregates only, write-once with verify); the measured costs come from [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) (USD 0.00016 per attempted case, USD 0.000561 per resolution for `router_v2`).

Stated on the page, not claimed: no measured saving, no price on an unsafe outcome, no saving from better handoffs, and no field resolution rate; the data does not separate dispute calls from other transactional calls, so the projection bounds the flow.
