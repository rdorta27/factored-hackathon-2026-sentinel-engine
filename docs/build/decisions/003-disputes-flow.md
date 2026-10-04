---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 003 · Initial flow: transaction disputes

**Date:** 2026-09-28 · **Updated:** 2026-09-29
**Status:** Accepted (confirmed at the 9/29 review; evidence in [flow selection](../flows/03-flow-selection.md))
**Participants:** Team

## Context

We must choose a flow to start the build on Tuesday, before the data profile is ready. The status presentation of 9/28 proposes transaction disputes as the start. It permits a change if the data analysis does not support it. The [candidate flows](../flows/01-flow-candidates.md) page gives the options and the comparison.

The flow must show all of these at the same time:

- Data analysis.
- A conversation that uses tools.
- An action that the user confirms and the system verifies.
- A handoff with evidence.
- A learned component against a baseline.

## Options

1. **Transaction disputes** (*transaction-dispute intake*): a visible action (the dispute opens), a natural handoff (fraud, high amount, complex case), 80K complaints and 5M transactions with `is_fraud`. Against: we do not know yet how many complaints are about charges, or if the labels work for ML.
2. **Accounts or payments:** the easiest and lowest risk. But almost everything is read-only, so the action and the handoff are weak.
3. **Cards:** a clear action (block, confirm, verify), but less data in the dataset.
4. **Credit:** a high risk to cross policy limits. A demo that is harder to defend.

## Decision

Confirmed on 9/29: **transaction disputes, entered through an account inquiry** ([flow selection](../flows/03-flow-selection.md)). We measured the Tuesday criteria below. Cards was the alternative that we did not take.

| Criterion | How we measure it | We stay with disputes if… | Result (measured 9/28, confirmed 9/29; [evidence](../flows/03-flow-selection.md)) |
|---|---|---|---|
| Relevant volume | Complaints with `case_type = Claim` and the unrecognized-charge category; their weight in `contact_reason` of `call_center_interactions` | The volume is sufficient to train and evaluate (threshold set after we see the distribution) | Low: 251 unrecognized-charge claims in Q4-2024 (about 2.7 a day), 4.47% of complaints. 35% transactional calls support the entry point. |
| Cross-source linkage | % of complaints with a valid `origin_interaction_id`; % of those interactions with a transcript | The chain call → transcript → complaint covers a useful share of cases | **Fails:** 0% of complaints have `origin_interaction_id`. The transcripts are templates. |
| Labels | Quality and balance of `category` / `subcategory` and of `was_escalated` | At least one label is consistent and not trivial | **Fails for complaints:** `description` leaks `category`. `was_escalated` exists only on calls (10%) and no single field predicts it. |
| Defensible ML | A keyword or TF-IDF baseline against a learned component, with a time split. The component can be a simple model or a few-shot LLM classifier. A prompted LLM counts as a learned component if we define, evaluate and justify it (REQ-0016). | The component beats the baseline on the same held-out set, with valid labels and no leakage | Decided 9/29: a prompted LLM on team-generated text ([decision 007](007-learned-component.md)). A multivariate check on call escalation is not part of the design. |
| Data leakage | Review of the features | Only fields known at opening time. Outcome fields (`status`, `resolution`, `sla_breached`, and others) stay out. | Done: we identified and banned the closing and post-opening fields. |

If the volume or the labels fail, the preferred alternative is **cards**, with the same structure: confirm, act, verify, and a handoff on fraud. A classical model with no margin over the baseline does not cause the switch, if the few-shot LLM approach is defensible.

## Consequences

- **Scope:** the assistant identifies the transaction, collects the data, shows verified facts, confirms the intent, opens the dispute, verifies that it exists, and gives the number and the next step. **It does not decide fraud or the outcome of the dispute.** The typical case is an unrecognized charge. In the dataset, a dispute is a `complaints` row with `case_type = Claim`.
- **PQR is not the scope:** the `complaints` table comes from the PQR system (*Peticiones, Quejas y Reclamos*: requests, complaints and claims). It has claims (`case_type = Claim`), complaints, requests and suggestions. We use it for analysis and ML. The flow serves only transaction disputes.
- **Handoff:** on suspected fraud, a high amount, a repeat customer, missing information, a policy limit, or a request of the customer. The package follows section 8 of the presentation: request, verified facts, transactions, actions taken, evidence, open questions and reason. *Updated 9/29:* `is_fraud` is a label known after the fact. It is never a runtime signal. The fraud rule uses the words of the customer and `fraud_score` ([010](010-fraud-handoff-rule.md)). Rules and thresholds: [specification](../../architecture/specification.md#decision-priority).
- **Dispute window:** a customer can dispute a charge up to **90 days** after its `transaction_date`. An older charge is not disputable: the assistant explains why and offers a handoff. This was an assumption of Natalia, with no confirmed source. It is in configuration as a synthetic policy, so the value can change per country. With static data, "today" is the simulated demo date, not the real date. *Updated 9/29:* Gold computes `is_eligible_for_dispute` when it builds, so the flag gets old between runs. The policy engine computes the window again at request time and uses the flag only as a hint ([data contract](../../architecture/specification.md#data-contract)). *Updated 10/2:* the sources do not support one 90-day window for the three countries ([021](021-dispute-policy-sources.md)).
- **Late arrivals:** if the charge does not appear, we open the dispute as *pending verification* ([conversation](../conversation.md)).
- **Portuguese:** the dataset is in Spanish only. [017](017-portuguese.md) defines the Portuguese test cases.
- **Refinement confirmed on 9/29 ([evidence](../flows/03-flow-selection.md#suggested-flow)):** the dispute starts as an account inquiry: first look up the charge and its status. The reasons: the demand is in transactional calls, and the dispute labels fail the ML criteria in every flow. The learned component becomes a prompted LLM on team-generated text ([decision 007](007-learned-component.md)).
- **Scope of the entry point:** charges and transactions only ([decision 008](008-account-inquiry-scope.md)).
- **Thresholds:** set from the development window ([010](010-fraud-handoff-rule.md), [011](011-high-amount-threshold.md)). The held-out acceptance rules are in [018](018-evaluation-acceptance.md).
