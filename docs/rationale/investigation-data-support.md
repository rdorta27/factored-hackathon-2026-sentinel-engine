---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# Investigation data support

## Choice

The assistant does not investigate a charge with balances, product status, complaint history or "unusual for you" signals. It uses the transaction status and the fraud-score rule only ([010](../build/decisions/010-fraud-handoff-rule.md)). The scope of [008](../build/decisions/008-account-inquiry-scope.md) does not change.

## Why

The team measured the dataset before it planned the feature. Two runs on the development zone (before 2025-07-01) gave a "no" to each signal:

| Signal we wanted | What the data shows | Field |
|---|---|---|
| Show the balance next to the movements | The balance has no usable as-of date. It does not follow the net flow of the movements. | [`dev-v1`](../../evidence/customer-360/dev-v1/summary.json): `balance.safe_to_show`, `balance.asof_usable`, `balance.spearman_by_currency` |
| "Your card is blocked, so this charge is suspicious" | Blocked, closed and suspended products have no transactions. The status has no change date. | `status.non_active_products_have_txns`, `status.status_change_date_available` |
| "This pending charge is a pre-authorization" | No pending charge has a later matching charge. | `status.pending_followed_pct` |
| "This charge is a duplicate" | The development transactions have no duplicates. | `status.exact_duplicate_rows_pct`, `status.near_duplicate_rows_pct` |
| "You already complained about this charge" | A complaint has no transaction or merchant field. Its product never belongs to the customer who complains. Amounts match no better than chance. | `complaints.charge_linkable`, `complaints.affected_product_owned_by_complainant_pct`, `complaints.amount_match` |
| "This charge is unusual for you" | No customer signal predicts `is_fraud`. No signal adds to `fraud_score`. | [`dev-signals-v1`](../../evidence/customer-360/dev-signals-v1/summary.json): `investigation.has_signal`, `incremental.per_signal` |

The fraud label is also an artefact of the data generator. A non-fraud charge never has a `fraud_score` above 30 (`labels.synthetic_artefact`). The p95 rule of decision 010 therefore sets a workload. It is not a fraud detector (`labels.p95_rule`). A rule at 30 would use the artefact, so we do not use it.

## Alternatives rejected

- **Build the investigation on these signals.** The answers would be wrong ("materially incorrect outcomes" in the brief).
- **Build it on invented test data.** The team would design the data and then measure its own design. The result would prove nothing.
- **Show the balance with a warning.** A wrong number with a warning is still a wrong number.

## In production

A bank has real balances with an as-of date, status history and complaints linked to transactions. The design stays the same: deterministic signals from Gold, decided in code, never by the model. Each signal must pass the same check before it goes live: coverage, lift on a real label and an added value over the existing score.

## Facts we can still show

The signals run can support facts, not risk claims. Examples: "you paid this merchant before", or "this charge is in another country". The merchant name is missing on most charges (`signals.per_signal.first_merchant`). These facts are in the roadmap, not in the demo.

## On the slide

"We measured before we built. The data cannot support a balance, a blocked card, a pre-authorization or a complaint history, so the assistant does not claim them."
