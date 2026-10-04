# Policy thresholds

Decisions [010](../build/decisions/010-fraud-handoff-rule.md) and [011](../build/decisions/011-high-amount-threshold.md). OpenSpec change `add-fraud-and-high-amount-rules`.

## Choice

Two handoff rules send a dispute to an advisor:

- **Suspected fraud:** the customer says the charge is not theirs (`fraud.claim`), or the `fraud_score` of the charge is above the threshold (`fraud.score`).
- **High amount:** the amount of the charge is above the threshold (`amount.high`).

Each threshold has one value per account country **and** charge currency. The values are a **synthetic policy** that the team wrote. A bank replaces them in configuration. The [policy sources](policy-sources.md) page lists the rest of the policy and where real values come from.

## Why

- **The brief asks the system to know when not to act.** It also asks for policy outside the model text (REQ-0006, REQ-0007, REQ-0033). Fraud and large amounts are where the system must not act alone.
- **The dataset has no bank policy.** We use the 95th percentile of the development window per country and currency. About 5% of charges go to a person. This is a **workload choice**, not a fraud detector.
- **One value per currency,** because currency belongs to the product ([data assumptions](data-assumptions.md)).
- **At least 100 charges per group.** A smaller group gets no rule. We report it as a limit.
- **Two rule ids for fraud.** The advisor and the logs show if the words of the customer or the score caused the handoff (REQ-0029). The customer never sees the word "fraud" or the score.
- **The score is the dataset column.** The rule never uses `is_fraud`, because a bank knows it only after an investigation.

## Evidence

| What | Field |
|---|---|
| The configured values | [`evaluation/2024Q4-v2`](../../evidence/evaluation/2024Q4-v2/summary.json): `account_thresholds.groups.<country>.<currency>`. A test fails if a configured value differs. |
| Five groups have enough data: AR ARS and USD, CO COP and USD, MX USD | `account_thresholds.groups.<country>.<currency>.n` |
| México has no MXN data | [`customer-360/dev-v1`](../../evidence/customer-360/dev-v1/summary.json): `products.by_country.México.currency` |
| The p95 score rule, re-derived on a later window: it fires on about 4% of charges, with low precision and about half the recall | [`customer-360/dev-signals-v1`](../../evidence/customer-360/dev-signals-v1/summary.json): `labels.p95_rule.precision_pct`, `labels.p95_rule.recall_pct` |
| A non-fraud charge never has a score above 30. This is an artefact of the generator. | `labels.synthetic_artefact` |
| The rules decide without an unsafe outcome on the attacks | [`adversarial/20261002T222323Z`](../../evidence/adversarial/20261002T222323Z/summary.json): `totals.unsafe_outcome_rate` |

The precision of the p95 rule is low because the fraud label is rare and has no structure in this dataset. A rule at a score of 30 would catch about the same frauds with no false alarm (`labels.bound_rule`). We do not use it, because it uses an artefact of the generator. A real bank score does not have this boundary.

## Alternatives rejected

- **One USD threshold on `amount_usd`.** The customer does not see a USD figure. The value uses fixed synthetic exchange rates. It is empty on every USD row and on about 5% of ARS and COP rows (`labels.amount_usd_fill_by_currency`). It does not cover the score.
- **A value on the 0 to 100 scale of the dictionary, for example 50.** Non-fraud scores stop at 30, so such a rule catches fraud only. It uses the artefact.
- **p90 or p99.** p90 doubles the advisor load. p99 almost never fires in the demo.

## How a bank changes them

1. Edit the country file in `sentinel-ai-core/config/policy/`: the `values` per currency, `source` for the policy reference, and `synthetic: false`.
2. No code change. The rule ids stay the same, so logs and handoffs stay comparable.
3. Each decision records the version of the policy file.
4. In production, the policy owner approves and versions the file ([path to production](../architecture/specification.md#path-to-production), REQ-0052).

## Limits we state

- A percentile sets the workload. It does not tell how many frauds the rule catches.
- A small currency group can have no rule.
- The "not mine" claim comes from the words of the customer. Evaluation cases measure its recall.

## On the slide

"Fraud and high amounts go to a person. With no bank policy, we set synthetic thresholds at the 95th percentile per country and currency: about 5% of charges. A bank replaces them in configuration, with no code change."
