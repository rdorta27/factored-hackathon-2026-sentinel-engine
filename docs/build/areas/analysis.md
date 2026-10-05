---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Data Analytics

**Evaluation criterion:** data quality and relevant insights from the solution.

**Owner:** Natalia.

**Requirements:** the requirements in the `analysis` area of the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../data/dataset.md), [metrics](../metrics.md) and [candidate flows](../flows/01-flow-candidates.md).

## Scope

- **Analysis that justifies the flow:** contact reasons, demand patterns, data quality and operational constraints. The analysis is reproducible. A notebook or a script gives the same figures each time that anyone runs it.
- **Baseline** and expected results for the customer and for the business.
- **Metrics reports:** scripts generate them from the logs (see [metrics](../metrics.md)).
- **Cost-per-resolution ROI**, labeled as projected savings.
- **Breakdown by language, country and segment**, with an investigation of each disparity.

## Sources for justifying the flow

| Source | What it shows |
|---|---|
| `call_center_interactions`, `call_transcripts`, `complaints`, `satisfaction_surveys` | Why customers make contact, how the bank resolves cases and how satisfied customers are |
| `transactions` | The context of charge disputes and fraud |

## App errors and demand

The analysis joins the `Error` events of `digital_events` with the interactions and the complaints, by customer and date. The join shows which failures cause contacts.

## Campaigns and demand

Campaigns (`marketing_campaigns`, `campaign_sends`) can explain a spike in contacts or complaints by date, country and product. The analysis that justifies the flow uses them.

## Sizing

REQ-0053. The dataset has about 730–900 call-center interactions a day (800K over three years). The sizing work does three things:

- It estimates how many of the interactions are disputes each day.
- It states the volume that the prototype is designed for.
- It states what changes at real volume.

The organizers value a clear statement of sizing limits as business judgment (help channel, 9/28). The prototype does not need to handle the full volume.

## Country monitoring

**This page owns this topic.** [Metrics](../metrics.md) (breakdown), [AI](ai.md) (observability) and the [requirements](../../requirements/requirements.md) (REQ-0050, country monitoring) link to it.

The bank operates in MX, CO and AR. The integrations differ in each country. A breakdown of latency, tool failures, handoffs and complaints by country shows operational problems. It also supports the fairness analysis. Country and accent are attributes that the data already has. They need no model.

The monitoring is implemented and has evidence:

- `sentinel-ai-core/eval/monitor.py` aggregates the turn log for each country and language.
- The aggregates are turns, p50 and p95 latency, failed or timed-out steps, handoffs, fallback turns and cost.
- The script keeps aggregates only. It reports a country outside MX, CO and AR apart. The run is write-once.
- The frozen evidence is [`evidence/monitoring/2024Q4-resolution-v2-replay/summary.json`](../../../evidence/monitoring/2024Q4-resolution-v2-replay/summary.json). It covers the simulated replay workload (256 turns, 888 records).
- The [metrics report](../metrics-report.md) (section 6, country monitoring) reports the result.
- A field run uses the same script on the Azure turn log. The repository does not hold that log.

## Credit limits

A learned segment (for example "premium") cannot change an eligibility rule. The policy service decides the rules. The system can use a segment to prioritize service. The analysis then measures the effect for each segment.

## Reusable dataset use cases

The overview proposes generic use cases. We use a use case only if it serves the flow. Examples: fraud detection (for cards or charge disputes), intent classification, first-contact resolution and sentiment trends.

## Evidence for evaluation

- [ ] Reproducible analysis that justifies the chosen flow
- [ ] Final metrics report: baseline and system
- [ ] ROI calculation with stated assumptions
- [ ] Limitations section

## Open questions

- Which cost assumptions do we use?
