# Data Analytics

**Evaluation criterion:** data quality and relevant insights from the solution. **Owner:** Natalia.

**Requirements:** those in the `analysis` area in the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../data/dataset.md), [metrics](../metrics.md), [candidate flows](../flows/01-flow-candidates.md).

## Scope

- **Analysis that justifies the flow**: contact reasons, demand patterns, data quality, operational constraints. It must be reproducible: a notebook or script that anyone can re-run and get the same figures.
- **Baseline** and expected results for customer and business.
- **Metrics reports** generated with scripts over the logs (see [metrics](../metrics.md)).
- **Cost-per-resolution ROI**, labeled as projected savings.
- **Breakdown by language, country, and segment**, with investigation of disparities.

## Sources for justifying the flow

`call_center_interactions`, `call_transcripts`, `complaints`, and `satisfaction_surveys`: why customers contact us, how cases are resolved, and how satisfied they are. `transactions` gives context for charge disputes and fraud.

## App errors and demand

We cross `Error` events from `digital_events` with interactions and complaints (by customer and date) to see which failures generate contacts.

## Campaigns and demand

Campaigns (`marketing_campaigns`, `campaign_sends`) may explain spikes in contacts or complaints by date, country, and product. We use them in the analysis that justifies the flow.

## Sizing

REQ-0053. The dataset has about 730–900 call-center interactions a day (800K over three years). We estimate how many of them are disputes per day, state the volume the prototype is designed for, and what would change at real volume. Recognizing sizing limits is valued as business judgment (help channel, 9/28); a prototype is not expected to handle the full volume.

## Country monitoring

**This document owns this topic.** It is linked from [metrics](../metrics.md) (breakdown), [AI](ai.md) (observability), and the [requirements](../../requirements/requirements.md) (REQ-0050, country monitoring).

The bank operates in MX, CO, and AR, with different integrations per country. Breaking down latency, tool failures, escalations, and complaints by country reveals operational problems and supports the fairness analysis. Country and accent are attributes already present in the data: they require no model.

The monitoring is implemented and evidenced: `sentinel-ai-core/eval/monitor.py` aggregates the turn log per country and language (turns, p50/p95 latency, failed or timed-out steps, escalations, handoffs, fallback turns, cost; aggregates only, a country outside MX, CO and AR reported apart, write-once). The frozen evidence is [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json) over the simulated replay workload (256 turns, 888 records), reported in the [metrics report](../metrics-report.md) (section 6, country monitoring). A field run would use the same script over the Azure turn log; that log is not committed.

## Credit limits

A learned segment (e.g., "premium") cannot change eligibility rules, which are decided by the policy service. It can be used to prioritize service, measuring the effect by segment.

## Reusable dataset use cases

The overview proposes generic use cases; we use them only if they serve the flow. Examples: fraud detection (for cards or charge disputes), intent classification, first-contact resolution, sentiment trends.

## Evidence for evaluation

- [ ] Reproducible analysis justifying the chosen flow
- [ ] Final metrics report: baseline vs. system
- [ ] ROI calculation with stated assumptions
- [ ] Limitations section

## Open questions

- What cost assumptions do we use?
