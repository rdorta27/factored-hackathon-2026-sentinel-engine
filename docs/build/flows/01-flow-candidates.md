---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Candidate flows

This page lists the four workflows that the hackathon offers. It gives what each workflow must demonstrate and how the team compares them. It is the first of three flow documents:

1. **Candidate flows** (this page): where the options come from.
2. [Flow measurements](02-flow-measurements.md): the exact results of the measurement script.
3. [Flow selection](03-flow-selection.md): what the results mean and why the team chose the flow ([decision 003](../decisions/003-disputes-flow.md)).

**Sources:** the hackathon brief (*Factored AI & Data Hackathon 2026*, section Scope), the kickoff (slide *Task selection*), the [dataset](../../data/dataset.md) and the data dictionary.

**Related:** [requirements](../../requirements/requirements.md) and [ML](../areas/ml.md).

## The brief

- **Pick one coherent workflow.** The brief names four examples ("such as"): account or payment inquiries, card-service support, transaction-dispute intake, and credit-product information and eligibility support. They are examples, not tracks. More workflows earn no bonus. Depth, demonstrated behavior and engineering judgment score.
- **Justify the choice with data.** The kickoff asks to "justify workflow selection using reproducible logs" (*Data-backed baseline*). The brief asks for an analysis of contact reasons, demand patterns, data quality and operational constraints. Documents 2 and 3 do this work.
- **Three cases in the demo:** a normal resolution path, an ambiguous or unsupported request, and a case that needs a human.
- **Spanish and Portuguese.** The report states the limits of the data and of the language coverage.
- **The system loop:** Understand → Decide → Act → Verify → Escalate. The report includes only actions whose outcome the system verified.
- **At least one learned component.** The team benchmarks it against a baseline on the same held-out data (data kept aside for the final evaluation). The labels are valid and the data has no leakage.

## The four flows

The flows follow the order of the brief. Each flow lists the problem, the data, the learned component, the controls in code, the handoff and the main risk.

### 1. Accounts and payments

**Problem:** transactional volume in the call center: balances, movements, and declined, pending or reversed payments. The assistant authenticates the customer and reads the movements. It explains the status with real data. It opens a dispute only if the customer does not recognize a charge.

- **Data:** `products` (balances, status), `transactions` (status Approved, Declined, Pending or Reversed; `merchant_category`; `channel`) and `call_center_interactions` (`contact_reason`).
- **Learned component:** an intent classifier. The baseline is TF-IDF with logistic regression. The challengers are embeddings or an LLM. The split is by time. The classifier uses only information that exists before the case.
- **Controls in code:** `get_transactions(customer_id)` validates the session. The LLM never decides an amount or a status.
- **Handoff:** the amount is above a threshold, or the customer insists.
- **Main risk:** almost everything is read-only, so the action and the handoff are thin.

### 2. Cards

**Problem:** "I lost my card", "my card is blocked", "why is it not working?". These requests need concrete actions with an explicit confirmation.

- **Data:** `products` (Credit or Debit Card; status Active, Blocked or Suspended), `transactions` (recent declines), `digital_events` and `call_center_interactions`.
- **Learned component:** an intent classifier and an "urgency or possible fraud" detector. The baseline is rules.
- **Controls in code:** a card state machine. Each action (`block_card`) needs a valid session and a confirmation. The system reports the action as done only if the tool confirmed it. A human always handles an unblock after fraud.
- **Handoff:** a card replacement, fraud or inconsistent data.
- **Main risk:** unknown before the measurement. We do not know how much demand for card support the call data shows.

### 3. Disputes

**Problem:** the customer does not recognize a charge and asks for a review. The assistant turns a free conversation into a well-formed dispute (category, linked transaction and evidence) and routes it. It does not decide the outcome.

- **Data:** `complaints` (`case_type = Claim`, `category`, `subcategory`, `reception_channel`, `status`), `transactions` and `satisfaction_surveys`.
- **Learned component:** a category classifier and an escalation-risk model. The baseline is keyword rules.
- **Controls in code:** the legal deadlines and the mandatory fields of each country are rules.
- **Handoff:** the package for the advisor (summary, verified facts, evidence and open questions) is the main deliverable.
- **Main risk:** unknown before the measurement. We do not know how many complaints are about charges. We do not know if the labels and the text support a classifier.

### 4. Credit

**Problem:** "Can I take a loan or raise my limit?". The assistant explains products with policy sources. It produces a **simulated** eligibility outcome from a synthetic rules service. It does not approve credit.

- **Data:** `customers`, `products` (loans, credit cards, balances), `transactions`, `marketing_campaigns` and `campaign_sends`.
- **Learned component:** risk estimation (gradient boosting). The brief requires that it stays separate from the eligibility policy and from the conversation.
- **Controls in code:** the policy service (rules labeled synthetic) produces the outcome. The LLM only communicates it. A human reviews borderline or incomplete cases.
- **Main risk:** this flow has the most requirements (fairness by segment, explanations and uncertainty) for a submission of ten days.

## Comparison criteria

The team asks the same four questions for each flow. The measurements in document 2 answer them:

| Question | Why it matters |
|---|---|
| Is there **demand**? | A flow that nobody needs gives a weak demo and a weak business case |
| Are there **operational data** to look up and act on? | The assistant must verify facts. It must not invent them |
| Is there **signal** for a learned component? | The brief requires one, evaluated against a baseline |
| Are the **labels and text** trustworthy? | A leaky label makes each metric meaningless |

The brief asks for one flow. The comparison ends in one choice ([decision 003](../decisions/003-disputes-flow.md)). This page does not choose technology. See [001](../decisions/001-azure-platform.md), [005](../decisions/005-backend.md), [006](../decisions/006-frontend.md) and the [system](../../architecture/system-architecture.md).
