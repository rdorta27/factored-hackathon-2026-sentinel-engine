# 003 · Initial flow: transaction disputes

**Date:** 2026-09-28
**Status:** Proposed (provisional until the Tuesday 9/29 review)
**Participants:** Team

## Context

We must choose a flow to start building on Tuesday, before having profiled the data. The 9/28 presentation (*decisiones-2*) proposes transaction disputes as the starting point and leaves the door open to change if the data analysis does not support it. Options and comparison in [flow options](../flows/options.md).

The flow must simultaneously demonstrate: data analysis, tool-using conversation, confirmed and verified action, evidence-backed handoff, and a learned component against a baseline.

## Options

1. **Transaction disputes** (*transaction-dispute intake*): visible action (opening the dispute), natural handoff (fraud, high amount, complex case), 80K complaints and 5M transactions with `is_fraud`. Against: we still do not know how many complaints are really charge-related or whether the labels work for ML.
2. **Accounts or payments:** the easiest and lowest-risk, but almost everything is read-only; action and handoff are weak.
3. **Cards:** clear action (block, confirm, and verify), but less native data.
4. **Credit:** high risk of crossing policy limits; harder demo to defend.

## Decision

We start with the **transaction-dispute flow** as our working hypothesis. We confirm or change it on Tuesday 9/29 according to the following criteria, measured on the real data.

| Criterion | How it is measured | We stay with disputes if… |
|---|---|---|
| Relevant volume | Complaints with `case_type = Claim` and unrecognized-charge category; their weight in `contact_reason` of `call_center_interactions` | There is enough volume to train and evaluate (threshold to set once we see the distribution) |
| Cross-source linkage | % of complaints with a valid `origin_interaction_id`; % of those interactions with a transcript | The call → transcript → complaint chain covers a useful share of cases |
| Labels | Quality and balance of `category` / `subcategory` and of `was_escalated` | At least one label is consistent and non-trivial |
| Defensible ML | Keyword baseline vs. a simple model, with a temporal split | The model beats the baseline and the baseline is nowhere near 100% (a sign of template-generated labels) |
| Data leakage | Feature review | Only opening-time fields are used; outcome fields (`status`, `resolution`, `sla_breached`, etc.) stay out |

If volume or ML fails, the preferred alternative is **cards** (same structure: confirm, act, verify, and handoff on fraud).

## Consequences

- **Scope:** the assistant identifies the transaction, gathers the data, shows verified facts, confirms intent, opens the dispute, verifies that it exists, and delivers the number and the next step. **It does not decide fraud or the dispute outcome.** The typical case is an unrecognized charge. In the dataset, a dispute corresponds to a `complaints` row with `case_type = Claim`.
- **PQR is not the scope:** the `complaints` table comes from the PQR system (*Peticiones, Quejas y Reclamos* — requests, complaints, and claims). Besides claims (`case_type = Claim`), it includes complaints, requests, and suggestions; we use it for analysis and ML, but the flow only serves transaction disputes.
- **Handoff:** on suspected fraud (`is_fraud` / `fraud_score`), high amount, repeat customer, insufficient information, policy limit, or customer request. The package follows section 8 of the presentation: request, verified facts, transactions, actions taken, evidence, open questions, and reason.
- **Dispute window:** a charge can be disputed up to **90 days** after its `transaction_date`; older charges cannot be disputed: the assistant explains why and offers a handoff. Natalia's assumption, source still to confirm; it lives in configuration as a synthetic policy, so the value can change per country. With static data, "today" is the simulated demo date, not the real one.
- **Late arrivals:** if the charge does not appear, we open the dispute as *pending verification* ([conversation](../conversation.md)).
- **Portuguese:** the dataset is Spanish-only; we define the Portuguese test cases in decision 15, which should be brought forward.
- **Pending:** set the numeric thresholds once we see the data; choose the learned component (decision 2) in the same review.
