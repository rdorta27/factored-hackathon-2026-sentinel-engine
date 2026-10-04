---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The first message of a chat is the first thing that a customer and a judge see. A probe of `router_v2` on 2026-10-02 ([chat behaviour plan](../../../team/chat-behavior-plan.md)) and the manual test of Felix on 2026-10-04 show the same gaps:

- "hola", "gracias" or "¿eres un bot?" get "I can only help with charges".
- "quiero ver el estado de mi último cargo" ("I want to see the status of my last charge") gets "which charge?".
- "¿por qué no puedo reclamar el de enero?" ("why can't I dispute the January one?") gets a generic answer. The explanation exists only as a follow-up to a refusal.
- "un cobro de mil pesos" ("a charge of one thousand pesos") does not find the 1,000 charge.

The brief asks the system to keep context, clarify ambiguity and explain decisions from rules (REQ-0001, REQ-0002, REQ-0029, REQ-0044).

## What Changes

- **Openers in code.** When the router labels a message `missing`, a deterministic check finds a greeting, thanks, a goodbye or "are you a bot". The reply is friendly, says what the assistant can do, and never hands off.
- **Charge status.** With the `status` label of [router v3](../router-v3/proposal.md), the reply gives the status, date and dispute eligibility of the verified charge. It opens no case. With `router_v2` or the baseline, the behavior stays as today.
- **Why for a named charge.** "¿Por qué no puedo reclamar el de enero?" grounds the charge and answers from the policy rule and its values, the same as the existing "why?" answer.
- **Amounts and dates in words.** The narrowing parsers read amounts in words in es-419 and pt-BR ("mil pesos", "setecientos", "mil reais") and more date phrases. A parsed value counts only if it matches a verified candidate.
- **Varied fixed wording.** Two or three reviewed variants per key and language, picked by a deterministic rule from the turn count. Verified values come from the candidate, never from the model.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `chat`: openers, charge status, why for a named charge, amounts in words, wording variants.

## Impact

- `sentinel-ai-core/app/orchestrator/step.py`, `app/ai/grounding.py`, `app/orchestrator/explanation.py`, locale files, tests, [conversation rules](../../../docs/build/conversation.md).
- `router-v3` measures the result in `eval-v8`, so this change merges before the v8 seal.

## Non-goals

- New model labels other than `status` (they belong to `router-v3`).
- Replies written by the model (step 5 of the chat behaviour plan).
- Changes to the keyword baseline.
- Loans, balances and other out-of-scope requests (decision 008).
