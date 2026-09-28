# Metrics

System metrics catalog.

**Purpose:** what we measure and how we report it. **Related:** [ML](areas/ml.md), [analysis](areas/analysis.md).

Numeric targets remain to be defined once we review the data and confirm the flow on Tuesday 9/29.

## Rules for all metrics

- **Top metrics** (highlighted in the kickoff): safe automated resolution, unsafe outcomes, and cost efficiency. The rest are supporting.
- We measure the baseline and the system on the **same held-out set**.
- **Two evaluation sets**, reported separately:
  - Realistic held-out: the real case mix. It yields the global metrics.
  - Adversarial set: injection, unauthorized access, expired sessions, tool failures.
- **Data split:** we order by time, without splitting the same case across both sides, and with features computed only from information prior to each case (detail in [ML](areas/ml.md#rigor)). The first ~70% goes to development (temporal cross-validation by batches is allowed); the last ~30% is the held-out, which we measure **only once** at the end. If we tune the system while looking at the held-out, it stops being held-out.
- Each result carries: sample size (n), case mix, model and prompt versions, and variability across runs.
- Split by **language** (ES / PT), by **country** (MX / CO / AR), and by customer **segment**; we flag small samples. Country monitoring is in [analysis](areas/analysis.md#country-monitoring).
- We label the measurement type: offline, simulation, or projected savings. We never present offline results as production improvement.
- We generate metrics with **reproducible scripts over the logs** (script or CLI), with no dashboard.

## 1. Outcome

| Metric | Formula | Note |
|---|---|---|
| **Safe automated resolution** | cases resolved correctly and per policy, without a human / all in-scope cases | Also report the share of cases where automation was attempted |
| Containment | cases without transfer / all cases | Not the same as resolving; read together with the previous one |
| Missed transfers | cases that needed a human and were not escalated / cases that needed a human | Requires reference labels |
| Unnecessary transfers | cases escalated that did not need it / escalated cases | Requires reference labels |
| Handoff quality | % of handoffs with request, verified facts, actions, evidence, and open questions | Validatable against the JSON schema |
| **Unsafe outcomes** | no. of unauthorized disclosures or actions, or materially incorrect outcomes / n | Always with denominator; 0 on a small sample is not zero risk |
| Latency p50 / p95 | 50th and 95th percentiles of end-to-end time per case | Do not use the average. High p95: abandonments, repeated requests, timeouts |
| **Cost per attempted case** | total cost / attempted cases | State assumptions |
| **Cost per successful resolution** | total cost / safe automated resolutions | "Undefined" if there are no resolutions |

### Cost and ROI example (projected savings, not measured)

> **ILLUSTRATIVE EXAMPLE. Do not use for decisions or quote in the presentation.** The values (USD 0.05 and USD 2) are invented to explain the calculation; the real ones come from our measurements and documented assumptions.

Illustrative assumptions: AI USD 0.05 per attempted case, 40% safe resolution, human USD 2 per case.

```
AI:      100 cases × 0.05 = USD   5
Human:    60 cases × 2    = USD 120
Total                     = USD 125  → USD 1.25 per case
Humans only: 100 × 2      = USD 200  → USD 2.00 per case
AI cost per successful resolution: 5 / 40 = USD 0.125
```

- We work in totals; we do not mix unit costs with totals.
- Savings depend mostly on the safe-resolution rate, not on AI cost.
- We always report it together with the unsafe-outcome rate.

## 2. Security and reliability

| Metric | Formula | Target |
|---|---|---|
| Unauthorized accesses | data delivered from another customer or without a valid session / attempts | 0 |
| Prompt-injection resistance | blocked attempts / attempts (ES and PT) | TBD |
| Actions reported without verification | no. of actions reported without tool confirmation | 0 |
| Tool-failure handling | failures handled with bounded retry, fallback, or escalation / injected failures | TBD |
| Expired sessions handled | cases asking for re-authentication / cases with expired session | TBD |
| Restricted data in external LLMs | no. of requests with restricted data | 0 |

## 3. Response quality

| Metric | Formula | Note |
|---|---|---|
| Responses with source | factual responses with a verifiable source / factual responses | Explainability |
| Ambiguity handling | ambiguous cases where it clarifies or abstains / ambiguous cases | Includes multilingual ambiguity |
| LLM-judge vs human agreement | % agreement on a validated sample | Only if we use an LLM judge; document rubric |

## 4. Learned component

At least one, always against a baseline and on held-out. With the transaction-dispute flow, the candidates are in [decision 003](decisions/003-disputes-flow.md); the detail is in [ML](areas/ml.md).

| Possible component | Metric | Possible baseline |
|---|---|---|
| Intent or reason classifier | accuracy, F1 per class | Keywords or majority class |
| Escalation predictor | AUC, missed and unnecessary transfers at the chosen threshold | Simple reason-based rules |
| Fraud detection (cards or disputes) | AUC, precision and recall at one threshold | Bank's existing `fraud_score` |
| Policy retrieval (RAG) | recall@k, MRR | BM25 |
| Risk model (if the flow is credit) | AUC, calibration | Logistic regression or fixed rule |

AUC measures **ranking** (0.5 = chance), not calibration or the threshold; the policy defines the threshold.

## 5. Data

| Metric | Formula |
|---|---|
| Data quality | % of records passing the contracts (types, nulls, ranges) |
| Freshness | time from when the fact occurs until the system sees it (see [glossary](../understand/glossary/glossary.en-us.md#data)) |
| Update test | the update fixture passes (yes / no) |

## Open questions

- What cost assumptions do we use (price per token, human-advisor cost)?
- How many held-out cases do we need per language for the comparison to be meaningful?
