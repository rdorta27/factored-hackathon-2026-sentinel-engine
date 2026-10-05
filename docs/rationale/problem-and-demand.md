---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Problem and demand

## Choice

The team chose transaction disputes, entered through an account inquiry
([003](../build/decisions/003-disputes-flow.md)). The problem numbers come
from one frozen run on the development zone:
[`evidence/problem/dev-v1`](../../evidence/problem/dev-v1/README.md).

## Why

The brief asks for a problem supported by data. The run measures four things:
first-contact resolution, calls a day, agent hours and missing values. Every
number is an aggregate of the dataset. The dataset is synthetic.

Four terms, defined once:

- **First-contact resolution (FCR).** A call is solved at the first contact
  when the dataset field `was_resolved` is true. The dataset does not tell if
  the customer called again.
- **Busy-day level.** The 95th percentile of the daily call counts. 95 of 100
  days are below it.
- **Agent hours.** Calls in the window times the mean handling time, in hours
  per month.
- **95% range.** The range where the true value falls with 95% confidence. A
  rate uses the Wilson method. The busy day and the highest day use a
  bootstrap over the days.

## Evidence

Each row cites a field of
[`summary.json`](../../evidence/problem/dev-v1/summary.json).

| What | Field | Value |
|---|---|---|
| Calls in the development window | `totals.calls` | 464,791 |
| Calls excluded at the held-out cut | `totals.excluded_heldout` | 217 |
| FCR, account inquiry (*Transaccional*) | `reasons.Transaccional.share_pct` | 91.44% [91.3, 91.57] |
| FCR, transaction dispute (*Queja*) | `reasons.Queja.share_pct` | 43.64% [43.29, 43.98] |
| Calls a day, account inquiry | `demand.account_or_payment_inquiry.per_day_mean` | 218.48 |
| Busy day, account inquiry | `demand.account_or_payment_inquiry.busy_day_p95` | 292 [289, 296] |
| Highest day, account inquiry | `demand.account_or_payment_inquiry.highest_day` | 332 [316, 332] |
| Calls a day, transaction dispute | `demand.transaction_dispute.per_day_mean` | 106.3 |
| Busy day, transaction dispute | `demand.transaction_dispute.busy_day_p95` | 145 [142, 148] |
| Agent hours a month, account inquiry | `hours.account_or_payment_inquiry.hours_per_month` | 408.03 (rank 1) |
| Agent hours a month, transaction dispute | `hours.transaction_dispute.hours_per_month` | 390.78 (rank 2) |
| Calls with no duration | `missing.duration_seconds.share_pct` | 14.0% |
| Calls that map to credit information | `demand.credit_information.calls` | 0 |

What the table says:

- **Demand sits in account inquiries.** The *Transaccional* reason carries
  162,770 calls, or 218 a day. A busy day reaches 292 calls.
- **The dispute is the hard case.** Only 43.64% of *Queja* calls end at the
  first contact, against 91.44% of *Transaccional* calls. The dispute reason
  uses 390.78 agent hours a month.
- **The chosen flow keeps both.** It starts as an account inquiry and opens a
  dispute only when it applies ([003](../build/decisions/003-disputes-flow.md),
  [008](../build/decisions/008-account-inquiry-scope.md)).
- **No call reason isolates credit information.** Its demand is not measurable
  from this table.

## What the data cannot say

- The dataset is synthetic. The numbers describe the dataset, not a real bank.
- The product field is empty on about 60% of transactional calls
  ([008](../build/decisions/008-account-inquiry-scope.md)). The mapping uses
  the reason for the call only.
- **The complaints do not link to a transaction.** `origin_interaction_id` is
  empty on every complaint, so the run cannot tie a call to a filed dispute
  ([`customer-360/dev-v1`](../../evidence/customer-360/dev-v1/README.md)).
- The dataset does not tell if the customer called again, so FCR is the
  dataset field only.
- 14.0% of calls have no duration. The run counts them and does not fill them.
- **The saving range is an offline projection** ([roi](../build/roi.md)). This
  run measures no saving.

## Alternatives rejected

- **Lead with the dispute volume.** Unrecognized-charge claims are about 2.7 a
  day ([flow selection](../build/flows/03-flow-selection.md)). The demand is in
  inquiries, not in claims.
- **Map the reason to a workflow by product.** The product field is empty on
  most transactional calls.
- **Report the projected peak.** The earlier peak was a projection. This run
  replaces it with a measured busy day.

## In production

A bank has real call reasons, a full product field and a link from a complaint
to a charge. The mapping and the run stay the same. The numbers change. The run
commits the mapping before the first number, so a different mapping is a new
run.

## On the slide

"Demand sits in account inquiries: 218 calls a day, 292 on a busy day, and
91.44% end at the first contact. Disputes are harder: 43.64%. The flow starts
as an inquiry and opens a dispute only when it applies."

Requirements: REQ-0014 and REQ-0053
([analytics](../requirements/analytics.md)), with the data limits of REQ-0013
([delivery](../requirements/delivery.md)).
