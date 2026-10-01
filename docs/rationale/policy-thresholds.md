# Policy thresholds

Status: values pending the evidence run `evidence/evaluation/2024Q4-v2/` (OpenSpec change `add-fraud-and-high-amount-rules`, decisions 25 and 26). The method below is settled.

## Choice

Two handoff rules send a dispute to an advisor:

- **Suspected fraud:** the customer says the charge was not theirs (`fraud.claim`), or the charge's `fraud_score` is above the threshold (`fraud.score`).
- **High amount:** the charge amount is above the threshold (`amount.high`).

Both thresholds are set per account country **and** per charge currency. They are a **synthetic policy** written by the team; a bank replaces them by configuration.

## Why

- **The brief asks the system to know when not to act** and to keep policy outside model prose (REQ-0006, REQ-0007, REQ-0033). Fraud and large amounts are where acting alone is unsafe.
- **The dataset ships no bank policy**, so the values must come from somewhere we can justify. We use the 95th percentile of the development window per country and currency: about 5% of charges go to a person. That is a **workload choice**, not a measure of fraud-detection precision.
- **Per currency, because currency belongs to the product** ([data assumptions](data-assumptions.md)): a Mexican USD account gets its own value instead of being skipped.
- **At least 100 charges per group.** Below that, a percentile rests on a handful of rows; the group gets no rule and we report it as a limitation.
- **Two rule ids for fraud,** so the advisor and the logs show whether the customer's words or the charge's score escalated the case (REQ-0029). The customer never sees the word fraud or the score.
- **The score is the dataset's own column.** `is_fraud` is never used: it is known only after an investigation, so using it would leak the answer.

## Alternatives rejected

- **One USD threshold on `amount_usd`:** the column may be empty, a USD figure is not what the customer sees, and it does not cover the score.
- **The dictionary's 0-100 scale (for example 50):** observed scores sit below about 30, so such a threshold would never fire.
- **p90 or p99:** p90 doubles the advisor load; p99 would almost never show in the demo.

## How a bank changes them

1. Edit the country file in `sentinel-ai-core/config/policy/`: per-currency `values`, `source` pointing to its policy reference, `synthetic: false`.
2. No code changes. Rule ids stay the same, so logs and handoffs remain comparable.
3. Every decision records the policy file version, so a past case shows the values in force when it was decided.
4. In production the file goes through approval by the policy owner and is versioned ([path to production](../architecture/specification.md#path-to-production), REQ-0052).

## Limits we state

- A percentile sets workload; it says nothing about how many frauds are caught.
- Small currency groups may have no rule.
- The not-mine claim is detected from wording; its recall is measured by evaluation cases, not assumed.

## On the slide

"Fraud and high amounts go to a person. Lacking a bank policy, we set synthetic thresholds at the 95th percentile per country and currency, about 5% of charges, and a bank replaces them in configuration without touching code."
