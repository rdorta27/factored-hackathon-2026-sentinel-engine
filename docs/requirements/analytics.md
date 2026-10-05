---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Requirements: Analytics

This page holds the analysis that justifies the flow. It also holds the metrics that prove that the system works. The [requirements index](requirements.md) holds the sources, the classification, the status counts and the dependency chains.

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

Use the dataset to show that the chosen flow matters. Show the contact reasons, the demand, the data quality and the operational constraints. Make the analysis reproducible.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0031](data-ml.md#req-0031). The analysis uses approved, labeled data.

**Evidence:** Proven by:

- The reproducible [flow measurements](../build/flows/02-flow-measurements.md) and the [flow selection](../build/flows/03-flow-selection.md).
- The problem run [`evidence/problem/dev-v1`](../../evidence/problem/dev-v1/README.md). It holds these values for the development zone: first-contact resolution by reason, calls a day by workflow (mean, busy day and highest day), agent hours a month and missing values.
- The reason-to-workflow mapping of that run. The team committed it before the first number.

<a id="req-0022"></a>
### REQ-0022 · Metrics with n, mix and variability

Each reported metric states how many cases it covers, the mix of the cases, the versions used and the variation between runs. The report includes the failures. It does not hide them.

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 5; Evaluation evidence

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0055](#req-0055). The page reports the held-out metrics with n and failures.

**Evidence:** Proven by [`evidence/evaluation-runs/2024Q4-eval-v8/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v8/summary.json). It holds n, the case mix, the model and prompt versions, the failures and the base-level 95% intervals. It also holds the stability over 3 recorded repetitions on the high-risk subset (`high_risk_repeats`) and the v8 metrics per candidate (`candidates.<name>.subtype`, `slots`, `drafts`, `unsafe_wording`). The [analysis run](../../evidence/evaluation-runs/2024Q4-analysis-v8/summary.json) adds the confusion by intent, language and country (`M1_errors`).

Missing: nothing for the router component.

Added by [`evidence-hardening`](../../openspec/changes/archive/2026-10-05-evidence-hardening/tasks.md): each summary reports the number of bases next to the number of cases (`bases` in `eval/metrics.py` and `eval/intervals.py`), and the intervals resample by base. The reports show both numbers. The gap run [`2024Q4-resolution-gap-v1`](../../evidence/evaluation-runs/2024Q4-resolution-gap-v1/summary.json) and the cut-off run [`2024Q4-cutoff-diagnosis-v1`](../../evidence/evaluation-runs/2024Q4-cutoff-diagnosis-v1/summary.json) carry their `bases`. Remaining: the 20-label human check (task 3.3, sample prepared in `eval/review/human-check-v1.md`) and the three repeats of the final measurement (task 3.5, post-freeze).

<a id="req-0024"></a>
### REQ-0024 · Breakdown by language, country and segment

Compare the outcomes by language, by country and by authorized customer segment. The segment is the `segment` column of `customers`: Premium, Plus, Basic and Student. Investigate the disparities. State the limits of small samples. Label offline results, simulations and projections separately.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: Evaluation evidence

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](#req-0022). The page breaks down the reported metrics by language and country.

**Evidence:** Proven by three items:

1. Accuracy per variant (es-MX, es-CO, es-AR, pt-BR) and per intent, with intervals and a paired loss per variant. The source is [`evidence/evaluation-runs/2024Q4-eval-v7/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) (`component.versions.<version>.breakdown`, `variant_losses`).
2. The [segment and multi-currency dispute breakdown report](../reports/req_0024_segment_breakdown_report.md). It covers transaction volume, eligibility rate and monetary exposure. It groups them by segment (Basic, Plus, Premium, Student) and by country and currency (MXN, COP, ARS, USD). The view `v_service_dispute_eligible_transactions` in `sentinel-data-engine/data/gold_bank.duckdb` backs it.
3. The system outcomes per language variant and per account country, with n and situation-level 95% intervals. The source is [`evidence/evaluation-runs/2024Q4-resolution-v2/summary.json`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) (`system.<version>.by_variant`, `by_country`). Each group has the label "descriptive". The [metrics report](../build/metrics-report.md) shows them.

The system outcomes have no breakdown by customer segment. The resolution cases carry no customer record, so there is no segment to group by. The segment figures in item 2 are dataset context. They do not measure how the system answers each segment.

<a id="req-0050"></a>
### REQ-0050 · Monitoring by country

Monitor latency, failures, escalations and complaints for each country.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15 · Own: [analysis](../build/areas/analysis.md#country-monitoring)

**Depends on:** [REQ-0024](#req-0024), [REQ-0025](non-functional.md#req-0025). Country monitoring reads the logs and the breakdown.

**Evidence:** Proven by two sources.

1. The [country log analytics report](../reports/req_0050_country_logs_report.md). It covers the digital event volumes (11.9M across México, Colombia and Argentina), the call center interaction counts and sentiment scores by country and channel, and the customer satisfaction survey averages. The sources are `bronze_digital_events`, `silver_call_center_interactions` and `silver_satisfaction_surveys` in `sentinel-data-engine/data/gold_bank.duckdb`.
2. The monitoring of the system itself. The script `sentinel-ai-core/eval/monitor.py` aggregates the app turn log for each country and language. It reports turns, p50 and p95 latency, failed or timed-out steps, escalations, handoffs, fallback turns and cost. It keeps aggregates only and is write-once. The run [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json) freezes the result for the simulated replay workload (256 turns, 888 records). The [metrics report](../build/metrics-report.md) shows it.
3. The saved queries for the public link, [`deploy/azure/queries.kql`](../../deploy/azure/queries.kql). They run in the Log Analytics workspace of the Container Apps environment. They report turns, p50 and p95 latency and cost by country, outcome and language, and the failed or timed-out steps and the handoffs. They return aggregates only, with no identifier.

<a id="req-0053"></a>
### REQ-0053 · Sizing and its limits

State how many disputes a day appear in the data. State the capacity that the prototype is designed for. State what changes at real volume (help channel, 9/28).

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Help channel (9/28)

**Depends on:** [REQ-0014](#req-0014). Sizing uses the dispute volumes from the analysis.

**Evidence:** Proven by the [sizing and capacity specification](../sizing-capacity.md). It gives the dispute volume and the daily load from the data. It gives the prototype capacity (DuckDB, SQLite, one instance) and what changes at real volume.

- The latency targets use the router latency that [`2024Q4-eval-v7`](../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) measures.
- [`problem/dev-v1`](../../evidence/problem/dev-v1/summary.json) measures the busy-day load: `demand.account_or_payment_inquiry.busy_day_p95` = 292 and `demand.transaction_dispute.busy_day_p95` = 145. The highest days are 332 and 169.
- The event peaks stay projections.
- The load run [`20261005T211031Z`](../../evidence/robustness/20261005T211031Z/summary.json) measures `/api/v1/chat` on one replica with recorded answers. At the deployed limits (0.5 vCPU, 1 GiB) the container reaches about 5 requests a second; the p95 rises to 918 ms at the target 20. The host reaches 17.51 requests a second. The small live run reaches 0.66 requests a second at the target 2. See [capacity and latency](../rationale/capacity-and-latency.md).

Limit: the load run uses a laptop or a local container, not the cloud replica. The live part is small. The event peaks stay projections.

<a id="req-0055"></a>
### REQ-0055 · Mandatory outcome metrics

Report the outcome metrics that the brief requires:

- safe automated resolution, and the share attempted,
- containment,
- escalation quality (missed and unnecessary transfers),
- unsafe outcomes, with counts and denominators,
- p50 and p95 latency,
- cost per attempted case and cost per successful resolution ("not defined" if there is none).

**Priority:** P0 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis, ml

**Source:** Problem statement: Evaluation evidence; What your solution should demonstrate 5 · Kickoff p. 12

**Depends on:** [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025). The metrics come from the held-out set. Latency and cost come from the logs.

**Evidence:** Proven by:

- The [metrics report](../build/metrics-report.md) on the frozen run [`2024Q4-eval-v8`](../../evidence/evaluation-runs/2024Q4-eval-v8/summary.json). It gives the v8 component metrics per candidate: kind accuracy, subtype accuracy, slot precision, rejected drafts, unsafe wording, cost and latency, each with its denominator (`candidates.<name>.*`). The attack block reports the unsafe wording of each candidate (`attacks.candidates.<name>.unsafe_wording`).
- The final resolution run [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json), with [`2024Q4-resolution-v1`](../../evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) beside it. It measures safe automated resolution over 56 cases in 14 situations on the final loop. Both versions resolve 16 of 56 cases, with 0 unsafe outcomes and 0 missed transfers. The cost per resolution is USD 0.000561 for `router_v2`. The run has the breakdown by variant and by country, with n, situation-level intervals and the label "descriptive". It verifies offline.
- The router reports tokens and cost for each turn (`tests/test_ai_router.py`).

Stated limits, not missing work:

- The resolution rate is a simulation over a mock store. It is not a field resolution rate.
- The pending status is not covered. The mock store has no `Pending` row.
- The system block of `eval-v7` does not replay offline (report section 9). The resolution runs do.

Added by [`evidence-hardening`](../../openspec/changes/archive/2026-10-05-evidence-hardening/tasks.md): the gap run [`2024Q4-resolution-gap-v1`](../../evidence/evaluation-runs/2024Q4-resolution-gap-v1/summary.json) states the ceiling of safe resolution (16 of 56) and the cases where the baseline and the router differ (0). The live timing rehearsal [`2024Q4-resolution-live-dev-v1`](../../evidence/evaluation-runs/2024Q4-resolution-live-dev-v1/summary.json) measures p50/p95 latency per model call and per conversation, and cost per attempted case and per resolution, from live model calls under a USD 1 cap. Remaining: the live run on the frozen build (task 2.4, post-freeze). Until then the latency of `resolution-v2` comes from a replay, and the report labels it as a replay.

<a id="req-0057"></a>
### REQ-0057 · Business outcomes and ROI

State the intended customer outcomes and business outcomes. Give the ROI as a cost per resolution against the baseline. Label projected savings as projections.

**Priority:** P1 · **Status:** Done · **Criterion:** Data Analytics · **Area:** analysis

**Source:** Problem statement: introduction; What your solution should demonstrate 1 · Kickoff p. 13

**Depends on:** [REQ-0055](#req-0055). The ROI uses the cost per resolution.

**Evidence:** Proven by the following items. The result is a projection. It is never a measured saving.

- [ROI](../build/roi.md) gives the break-even safe-resolution rate: 0.21% to 2.99%. The range uses an assumed advisor-hour cost of USD 5 to 25 and an estimated infrastructure cost of USD 20 to 60 a month. Each input has a label for its origin. The page also has the sensitivity table and the measured simulated rate (16 of 56 = 0.2857, a simulation over the mock store).
- [`evidence/roi/2023-2026-callcenter-v1/summary.json`](../../evidence/roi/2023-2026-callcenter-v1/summary.json) freezes the call-center aggregates behind it: 240,056 transactional calls, 3.68-minute mean handle time, 0.9151 first-contact resolution and 0.0993 escalation. It keeps aggregates only. It is write-once and has a verify step.
- [`2024Q4-resolution-v2`](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) gives the measured costs: USD 0.00016 per attempted case and USD 0.000561 per resolution for `router_v2`.

The page states these limits and does not claim more:

- no measured saving,
- no price on an unsafe outcome,
- no saving from better handoffs,
- no field resolution rate.

The data does not separate dispute calls from other transactional calls. For this reason, the projection bounds the flow.
