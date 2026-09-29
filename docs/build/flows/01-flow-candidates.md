# Candidate flows

The four workflows the hackathon offers, what each must demonstrate, and how they are compared. First of three flow documents:

1. **Candidate flows** (this page): where the options come from.
2. [Flow measurements](02-flow-measurements.md): exact results of the measurement script.
3. [Flow selection](03-flow-selection.md): what the results mean and why the flow was chosen ([decision 003](../decisions/003-disputes-flow.md)).

**Sources:** the hackathon brief (*Factored AI & Data Hackathon 2026*, section Scope), the kickoff (slide *Task selection*), the [dataset](../../understand/dataset.md) and the data dictionary. **Related:** [requirements](../../requirements/requirements.md), [ML](../areas/ml.md).

## The brief

- **Pick one coherent workflow.** The brief names four "such as" examples: account or payment inquiries, card-service support, transaction-dispute intake, and credit-product information and eligibility support. They are examples, not tracks, and implementing more workflows earns no bonus. Depth, demonstrated behavior and engineering judgment are what score.
- **Justify the choice with data.** The kickoff asks to "justify workflow selection using reproducible logs" (*Data-backed baseline*), and the brief asks to analyze contact reasons, demand patterns, data quality and operational constraints. That is the job of documents 2 and 3.
- **Three cases in the demo:** a normal resolution path, an ambiguous or unsupported request, and a case that needs a human.
- **Spanish and Portuguese**, and an honest report of the limits in the data and in language coverage.
- **The system loop:** Understand → Decide → Act → Verify → Escalate. Report only actions whose outcome the system has verified.
- **At least one learned component, benchmarked against a baseline** on the same held-out data (kept aside for the final evaluation), with valid labels and leakage prevention.

## The four flows

In the order of the brief. Each lists the problem, data, learned component, controls kept in code, handoff and main risk.

### 1. Accounts and payments

**Problem:** call-center transactional volume: balances, movements, and declined, pending or reversed payments. The assistant authenticates the customer, reads movements, explains the status with real data, and opens a dispute only if the customer does not recognize a charge.

- **Data:** `products` (balances, status), `transactions` (status Approved, Declined, Pending, Reversed; `merchant_category`; `channel`), `call_center_interactions` (`contact_reason`).
- **Learned component:** an intent classifier (TF-IDF with logistic regression as baseline, against embeddings or an LLM), split by time and using only information known before the case.
- **Controls in code:** `get_transactions(customer_id)` validates the session; the LLM never decides amounts or statuses.
- **Handoff:** amount above a threshold, or an insistent customer.
- **Main risk:** almost everything is read-only, so action and handoff are thin.

### 2. Cards

**Problem:** "I lost my card", "my card is blocked", "why is it not working?". Concrete actions that need explicit confirmation.

- **Data:** `products` (Credit or Debit Card; status Active, Blocked, Suspended), `transactions` (recent declines), `digital_events`, `call_center_interactions`.
- **Learned component:** an intent classifier and an "urgency or possible fraud" detector, against rules.
- **Controls in code:** a card state machine; every action (`block_card`) needs a valid session and confirmation, and is reported as done only if the tool confirmed it. Unblocking after fraud always goes to a human.
- **Handoff:** card replacement, fraud, or inconsistent data.
- **Main risk:** unknown before measuring: how much demand for card support the call data shows.

### 3. Disputes

**Problem:** the customer does not recognize a charge and asks for it to be reviewed. The assistant turns free conversation into a well-formed dispute (category, linked transaction, evidence) and routes it. It does not decide the outcome.

- **Data:** `complaints` (`case_type = Claim`, `category`, `subcategory`, `reception_channel`, `status`), `transactions`, `satisfaction_surveys`.
- **Learned component:** a category classifier and an escalation-risk model, against keyword rules.
- **Controls in code:** legal deadlines and mandatory fields per country as rules.
- **Handoff:** the package for the advisor (summary, verified facts, evidence, open questions) is the main deliverable.
- **Main risk:** unknown before measuring: how many complaints are really about charges, and whether the labels and text support a classifier.

### 4. Credit

**Problem:** "Can I take a loan or raise my limit?". The assistant explains products with policy sources and produces a **simulated** eligibility outcome from a synthetic rules service, without approving credit.

- **Data:** `customers`, `products` (loans, credit cards, balances), `transactions`, `marketing_campaigns`, `campaign_sends`.
- **Learned component:** risk estimation (gradient boosting), kept separate from the eligibility policy and from the conversation, as the brief requires.
- **Controls in code:** the policy service (rules labeled synthetic) produces the outcome; the LLM only communicates it. Borderline or incomplete cases go to human review.
- **Main risk:** the most requirements (fairness by segment, explanations, uncertainty) for a ten-day submission.

## Comparison criteria

The same four questions for every flow, answered with the measurements in document 2:

| Question | Why it matters |
|---|---|
| Is there **demand**? | A flow nobody needs is a weak demo and a weak business case |
| Are there **operational data** to look up and act on? | The assistant must verify facts, not invent them |
| Is there **signal** for a learned component? | The brief requires one, evaluated against a baseline |
| Are the **labels and text** trustworthy? | A leaky label makes any metric meaningless |

The brief asks for one flow, so the comparison ends in one choice ([decision 003](../decisions/003-disputes-flow.md)). Technology choices are not made here: see [001](../decisions/001-azure-platform.md), [005](../decisions/005-backend.md), [006](../decisions/006-frontend.md) and the [architecture](../../understand/architecture.md).
