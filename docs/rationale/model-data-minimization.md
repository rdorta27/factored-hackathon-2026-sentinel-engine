---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# What the model never receives

## Choice

The language model receives the customer message and a short window of recent turns. Code masks personal data in the message before the call. The model never receives the customer id, the session, personal data or the fraud score of a charge. The policy engine reads the score from Gold, in code, and decides.

## Why

- **The customer never sees the model output.** The router returns an internal label: intent, language and the "not mine" claim. The reply comes from templates and verified Gold facts. So the question is what leaves the bank, not what the customer sees.
- **Minimization.** A call to a hosted model sends data to a third party. The brief forbids restricted data in external model requests (REQ-0047). The fraud score is not personal data. It is an internal risk signal, and the model has no use for it.
- **Policy decides, the model labels** (REQ-0033, REQ-0048). The model cannot reason about fraud, because it never gets the score. Code makes this true, not an instruction in the prompt.
- **Code enforces it.** The request builder refuses a charge field outside an allow-list before the call. A test fails if the score gets into a request.

## Evidence

| Check | Where | Result |
|---|---|---|
| The router request never carries the fraud score | `sentinel-ai-core/tests/test_ai_router.py::test_router_request_never_carries_the_fraud_score` | passes in CI |
| A national id typed by the customer never reaches the model | attack A9 in [`adversarial/20261002T222323Z`](../../evidence/adversarial/20261002T222323Z/summary.json) | `blocked_verified`, passed |
| Masked text does not leak downstream | `sentinel-ai-core/tests/privacy/test_no_leak_downstream.py`, `test_masking.py` | passes in CI |
| Turn records hold no personal data | `app/observability/records.py` refuses a personal-data field | enforced in code |

## Alternatives rejected

- **Send the score, because it is not personal data.** This adds an external data flow with no benefit.
- **Tell the model to ignore it.** An instruction is not a control (REQ-0007).

## In production

The same allow-list applies to every model provider. A new field in the list is a reviewed change. The request log records which fields went out.

## On the slide

"The model gets the customer's words, with personal data masked. It gets no ids, no personal data and no risk score. Code reads those and decides."
