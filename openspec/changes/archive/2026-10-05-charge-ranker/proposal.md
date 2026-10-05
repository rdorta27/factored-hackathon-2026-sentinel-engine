---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

Picking the right charge is the riskiest step of the chat. A wrong pick leads to a dispute on the wrong charge. Today, hand-written rules read the amount, the date and the merchant words, and narrow the list. We tested them on 24 cases only. They miss phrasings, for example amounts in words.

The brief asks for a learned part that is compared with a simple reference on held-out cases, with valid labels and no leakage. We have one learned part, the router, and a model wrote its test cases. A charge selector is a second learned part with exact labels: we know which real transaction each description points to, so no one labels by hand.

## What Changes

- **A set of examples built from real transactions.** A script reads the local dataset and writes a description of one charge, in es-419 and pt-BR, with noise: partial merchant names, amounts in digits or words, relative dates. It uses a fixed seed and writes no rows to git.
- **A small scoring model** (a logistic regression: it adds up weighted clues). For each description and charge, it reads 20 to 30 clues, such as how close the amounts are. It ranks the customer's charges from most to least likely.
- **A decision rule.** The system picks a charge alone only when the model is sure. The threshold is set on validation data so that wrong picks stay at 1% or less. If the model is not sure, the system shows the short list and asks, as it does today.
- **A fair comparison on one held-out set** of four configurations: the current rules (`rules_fixed`), the rules after `chat-start` (`rules_tuned`), the learned selector (`learned`) and the language-model reading (`LLM`, on a sample).
- **Safe splits and a locked model.** Test customers never appear in training, and the test set is later in time. New phrasing families appear only in test. The model file is tied to a hash, and the evaluation script cannot import the training code.
- **A switch, off by default.** It turns on only if the selector beats the rules with no extra wrong picks, and the owner approves.

## Capabilities

### New Capabilities
- `charge-ranking`: the learned charge selector, its evidence and its serving rule.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/ai/charge_ranker.py` (new), a generator and an evaluation script in `sentinel-ai-core/eval/`, `evidence/charge-ranker/`, a new decision 025, `docs/rationale/`, `evidence/README.md`, REQ-0016 and REQ-0017 evidence.
- Not changed: the policy, the confirm box, the router, the baseline and `app/ai/grounding.py` (the selector only imports it).

## Non-goals

- A change to who decides: the confirm box still shows the picked charge, and code still checks that the charge belongs to the customer.
- Rows of the dataset in git, or personal data in the model file (it holds weights only).
- Any use of the selector in the public demo before it passes the serving rule.
