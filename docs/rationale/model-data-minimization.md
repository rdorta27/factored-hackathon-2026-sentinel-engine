# What the model never receives

## Choice

The language model receives only the customer's message and a short window of recent turns. It never receives the customer id, the session, personal data, or the transaction's fraud score. The policy engine, in code, reads the score from Gold and decides.

## Why

- **The customer never sees the model's output.** The router returns an internal classification (intent and language). Replies are built from templates and verified Gold facts, so the question is not what the customer sees but what leaves the bank.
- **Minimization:** a call to a hosted model sends data to a third party. The brief forbids restricted data in external model requests (REQ-0047). The fraud score is not personal data, but it is an internal risk signal the model has no use for, so it stays inside.
- **Policy decides, the model converses** (REQ-0033, REQ-0048). If the model saw the score it could start reasoning about fraud; keeping it out makes that impossible by construction, not by instruction.
- **Enforced in code, not in the prompt:** the request builder rejects any charge field outside a whitelist before anything is sent, and a test fails if the score is passed.

## Alternatives rejected

- **Send the score because it is not personal data:** adds an external data flow with no benefit.
- **Ask the model to ignore it:** an instruction is not a control (REQ-0007).

## In production

The same whitelist applies to any model provider; adding a field to it is a reviewed change, and the request log records which fields were sent.

## On the slide

"The model gets the customer's words and nothing else it does not need: no ids, no personal data, no risk scores. Policy reads those in code."
