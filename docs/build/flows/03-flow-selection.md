---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Flow selection

This page explains why the data supports the chosen flow. It is the last of three flow documents: [candidate flows](01-flow-candidates.md), [measurements](02-flow-measurements.md) and this analysis. The measurements page gives the exact results. Each figure below cites one of its fields.

## Conclusion

**Chosen flow: transaction disputes, entered through an account inquiry** ([decision 003](../decisions/003-disputes-flow.md)).

- **Demand is in inquiries, not in disputes.** 35% of calls are transactional (about 213 a day). Claims of an unrecognized charge are about 2.7 a day. If the count includes the same subcategory filed as a complaint, they are 862 a quarter (about 9 a day). The flow starts as an account inquiry. It opens a dispute only when a dispute applies.
- **The value of disputes is controlled action.** The system looks up the charge, confirms, opens the dispute, verifies it and hands off with evidence. The brief asks the team to demonstrate this.
- **No flow gives a usable signal from one column.** The learned component is a prompted LLM. We compare it with a keyword baseline on the same held-out cases. It is not a classifier on tabular fields.

The analysis uses the development window only (2024-10-01 to 2024-12-31, by event date). The team reserved the data from 2025-07-01 for the final evaluation and did not read it.

The measured problem behind the flow is in [`evidence/problem/dev-v1`](../../../evidence/problem/dev-v1/README.md) and on the [problem and demand](../../rationale/problem-and-demand.md) page. It has first-contact resolution by reason, calls a day by workflow, and agent hours a month over the whole development zone (2023-06-17 to 2025-07-01).

**Terms.**

- *Handoff*: the system passes a case to a human advisor with a structured package.
- *Held-out*: data kept aside to measure the finished system.
- *Leak*: a field that already contains the answer, or that exists only afterwards.

## Method

Each flow answers four questions: demand, operational data, signal for a learned component, and trustworthy labels and text ([criteria](01-flow-candidates.md#comparison-criteria)).

- **Signal test.** For each target, the script splits the rows by one field at a time. It takes the **spread**: the highest group rate minus the lowest group rate (5.0% and 4.5% give 0.5%). Under about 1%, the field says almost nothing about the target. This is a one-field screen. It does not rule out a model that combines fields. The code fixes the `*_learnable` flags.
- **Timing constraint.** A field can be a feature only if it exists when the customer writes to the assistant. Fields that the bank fills in later (outcome, assignee, response date) tell the model the future. They work well on past data. They are empty in production.

## Summary

The rows follow the order of the brief. *Rank* orders the flows by what the data supports, whatever the decision (1 is the strongest).

| # | Flow | Demand | Data to act on | Signal for ML | Labels and text | Rank |
|---|---|---|---|---|---|---|
| 1 | Accounts and payments | **High:** 35% of calls | Good | Flat | Product blank on 60% of transactional calls | **1** |
| 2 | Cards | Not measurable | Fair | Flat | — | 3 |
| 3 | Disputes | Low: about 2.7 claims a day | Good | Flat | Label leak, template text, no link to calls | 2 |
| 4 | Credit | Not measured | Biased snapshot | Flat | — | 4 |

## 1. Accounts and payments

This flow covers balances, movements, and the reason why a payment is declined, pending or reversed.

| Measured | Value | Field |
|---|---|---|
| *Transaccional* (transactional) calls | 19,630 of 56,045 = 35.03%, about 213 a day | `accounts.reason_transaccional`, `accounts.n_calls` |
| Transactions: Approved · Declined · Pending · Reversed | 340,929 · 18,652 · 7,316 · 3,762 of 370,659 (91.98% · 5.03% · 1.97% · 1.01%) | `accounts.status_*` |
| Largest spread of the non-approved rate | 0.71% (channel) | `accounts.decline_spread_pp` |
| Transactional calls with a blank product field | 11,776 = 59.99% | `accounts.transaccional_products_blank` |

- **Strongest demand and checkable data.** Each transaction has a status that the assistant can read and explain.
- **Almost entirely read-only.** The flow shows little action and little handoff. No single field separates the non-approved transactions (8.02%; spreads 0.5% to 0.71%).
- Nobody can explain the blank product field. The analysis does not use it to tell which product a call was about.

**Verdict:** this flow has the best demand and the best data. It supplies the entry point of the chosen flow.

## 2. Cards

This flow blocks a lost card or explains a block, with an explicit confirmation.

| Measured | Value | Field |
|---|---|---|
| Credit cards in the snapshot | 81,895 | `cards.credit_cards` |
| Products Blocked (all types) | 16,233 = 4.96% of all products | `cards.blocked`, `credit.n_products` |
| Fraud transactions | 366 = 0.10% | `cards.fraud_true`, `accounts.n_transactions` |
| Spread of Blocked by product type | 0.98% | `cards.blocked_spread_pp` |

- **Clear action, thin evidence.** Calls cannot isolate cards: `reason_category` only mirrors `contact_reason` (`accounts.reason_category_degenerate`). Demand is not measurable. This is a gap in the evidence. It is not proof of zero demand.
- **Fraud is rare and belongs to a person.** 366 cases justify a handoff rule. They are not enough to train a model. A declaration of fraud moves money and has legal weight.
- The 4.96% covers every product type, not only cards.

**Verdict:** this flow was the fallback if disputes failed. The evidence is weak in both directions.

## 3. Disputes

The customer does not recognize a charge. The assistant finds the charge, opens a dispute and verifies it. It hands off with evidence when it must not act.

| Measured | Value | Field |
|---|---|---|
| *Cargo no reconocido* (unrecognized charge) claims | 251 of 5,611 complaints = 4.47% ±0.54%, about 2.7 a day | `disputes.unrecognized_claim`, `disputes.n`, `dispute_share_pct` |
| `description` contains `category` | 5,611 of 5,611 | `disputes.description_leak` |
| Complaints with `origin_interaction_id` | 0 | `disputes.linkage_filled` |
| Distinct 60-character transcript openings | 2 across 14,023 transcripts | `disputes.text_prefixes`, `disputes.transcripts` |
| Call escalation | 5,635 of 56,045 = 10.05% | `disputes.escalated_calls` |

- **Low demand.** The demo shows controlled action. It is not a volume story.
- **Label leak.** `description` already contains the category. A prediction of the category from the description scores high for the wrong reason. We rule out that classifier.
- **No link from call to complaint.** The column exists but is empty. Nobody can attribute a share of disputes to calls.
- **Text from templates.** We write the conversations in es-419 and pt-BR for the project. We label them as simulation.
- **Banned features (timing constraint).**
  - Closing fields are 0% filled while a case is open: `resolution`, `closing_date`, `compensation_granted`, `resolution_satisfaction` and others.
  - The assignment and first-response fields fill in after the case opens (about 50–57% for open cases, about 91–92% for closed cases).
  - `sla_breached` is always filled. It carries no signal (`disputes.leak_fill_*`).
- **Flat signal.**
  - Unrecognized-charge claim rate: the spread is 0.96% across priority and 4.72% across reception channel. The Regulator channel drives the second spread (46 complaints, 10 of them claims). The script reads it as small-sample noise.
  - Call escalation: the spread is 0.65% to 1.59% across channel, type, reason, wait and accent. By agent it is 0% to 26.7% among agents with 20 calls or more. The script reads this as routing, not customer need.
  - Fields: `disputes.cnr_spread_pp`, `disputes.regulator_n`, `disputes.esc_spread_pp`, `disputes.esc_agent_spread_pp`.

**Verdict:** the data supports this flow for action, verification and handoff. It does not support it for demand or for a classical model.

## 4. Credit

This flow explains products and gives a simulated eligibility outcome.

| Measured | Value | Field |
|---|---|---|
| Products in the filtered snapshot | 327,035 | `credit.n_products` |
| Products with days past due above 0 | 15,321 = 4.68% | `credit.delinquent` |
| Spread of the share above 30 days past due, three loan types | 0.48% | `credit.delinq_spread_pp` |

- **No demand measured.** This flow has the highest policy risk. The brief requires the team to separate the conversation, the risk estimate and the policy. It also requires fairness and explanations.
- **Biased snapshot.** `products` is one snapshot that `last_updated` filters. It shows the products that changed in Q4, not the real portfolio. It holds dates as late as 2027 ([dataset](../../data/dataset.md)).
- **Flat signal** by loan type.

**Verdict:** discarded.

## Suggested flow

"I don't recognize this charge" starts as an account inquiry about charges. It becomes a dispute only when it must. Balances, products, cards and credit are out of scope ([system: scope](../../architecture/specification.md#scope)). The steps are the loop that the brief asks for: Understand → Decide → Act → Verify → Escalate. The [system](../../architecture/system-architecture.md#walkthrough-of-a-case) page has the full sequence and the tool contracts. The [demo](../../architecture/demo-architecture.md#mocked-components) page shows which boxes are mocked.

```mermaid
flowchart LR
    customer(["Customer<br/>'I don't recognize this charge'"])
    subgraph system["The assistant"]
        direction LR
        understand["1 · Understand<br/><b>LLM</b>: intent, language,<br/>charge hints"]
        lookup["Look up<br/><b>Code</b>: customer's charges,<br/>status, as-of date"]
        decide{"2 · Decide<br/><b>Policy</b> first, then<br/>dispute <b>category</b>"}
        act["3 · Act<br/><b>Code</b>: confirm and<br/>open the dispute"]
        verify["4 · Verify<br/><b>Code</b>: read the<br/>dispute back"]
        respond["Reply<br/><b>LLM</b>: explanation or<br/>case number"]
        handoff["5 · Escalate<br/>JSON handoff: facts,<br/>evidence, open questions"]
    end
    gold[("Gold<br/>charges")]
    record[("Dispute record<br/>SQLite in the demo")]
    advisor(["Human advisor"])

    customer --> understand --> lookup --> decide
    lookup <--> gold
    decide -- "Pending, Reversed<br/>or Declined: explain" --> respond
    decide -- "dispute applies" --> act --> verify --> respond
    act --> record
    verify <--> record
    verify -- "not verified" --> handoff
    decide -- "suspected fraud, high amount,<br/>asks for a person, missing info" --> handoff --> advisor
    respond --> customer

    classDef ai fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef code fill:#ffffff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef dec fill:#fff0f5,stroke:#ff4f8b,stroke-width:2px,color:#1a1530
    classDef store fill:#fbfaff,stroke:#3d8bff,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class understand,respond ai
    class lookup,act,verify,handoff code
    class decide dec
    class gold,record store
    class customer,advisor ext
    style system fill:#fbfaff,stroke:#6d4aff,stroke-width:2px,stroke-dasharray:8 4
```

Legend: violet fill = LLM. Violet outline = code. Rose = decision (policy and learned component). Blue = data store. Grey = outside the system. The colors follow [`branding/`](../../../branding/BRANDING.md).

**Why this shape:**

- Demand is in inquiries (35% of calls), not in disputes (about 3 a day).
- A check of the status first avoids needless disputes (3% of transactions are Pending or Reversed).
- The hackathon brief emphasizes opening, verifying and handing off with evidence.

## Consequences for the design

- **Learned component:** a prompted LLM. We compare it with a keyword baseline on the same held-out cases ([REQ-0016](../../requirements/requirements.md)). The text is Latin American Spanish (es-419) and Brazilian Portuguese (pt-BR), written for the project and declared as such. The leak rules out a classification of `category` from `description`.
- **Entry point:** the flow starts as an account inquiry. The demand of the first option therefore carries the disputes flow. The inquiry covers charges and transactions only. This flow does not serve the demand for balances and products.
- **Suspected fraud** is a handoff rule in code. It is not a model. The rule uses what exists at runtime (the statement of the customer and `fraud_score`). It never uses `is_fraud`, a label that exists only after the fact. The threshold is open (decision 25).
- **Placement of the learned component:** the category that it assigns fills the dispute record. It does not decide whether a dispute applies.
- **Evaluation set:** the team writes it for the project and labels it as simulation.

## Limitations

- The results describe one quarter (Q4-2024). The text comes from templates, so the conversational results are simulation.
- The spreads test one field at a time. The team did not fit a model that combines fields (for example, for call escalation). Such a model extends the design. It does not change the flow.
- The calls could not measure the demand for cards and credit.
