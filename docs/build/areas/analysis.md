# Data Analytics

**Evaluation criterion:** data quality and relevant insights from the solution. **Owner:** Natalia.

**Requirements:** those in the `analysis` area in the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../understand/dataset.md), [metrics](../metrics.md), [flow options](../flows/options.md).

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

## Country monitoring

**This document owns this topic.** It is linked from [metrics](../metrics.md) (breakdown), [AI](ai.md) (observability), and the [requirements](../../requirements/requirements.md) (REQ-0050, country monitoring).

The bank operates in MX, CO, and AR, with different integrations per country. Breaking down latency, tool failures, escalations, and complaints by country reveals operational problems and supports the fairness analysis. Country and accent are attributes already present in the data: they require no model.

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
