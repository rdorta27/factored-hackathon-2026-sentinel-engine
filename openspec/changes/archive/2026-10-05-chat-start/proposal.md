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
- "¿por qué no puedo reclamar el de enero?" ("why can't I dispute the January one?") gets a generic answer (Felix 6).
- "un cobro de mil pesos" ("a charge of one thousand pesos") finds nothing (Felix 8).
- Every reply is one fixed sentence.

[`router-v3`](../archive/2026-10-05-router-v3/proposal.md) makes the model read more (contract v3). This change makes the loop use it, with a code fallback when `router_v2` or the baseline serves (REQ-0001, REQ-0002, REQ-0029, REQ-0044).

## What Changes

- **Openers:** a `missing` result with a subtype (greeting, thanks, goodbye, identity, help) gets a friendly reply and what the assistant can do, never a handoff. Without a subtype (v2, baseline), short patterns in code find the opener.
- **Charge status:** a `status` result gets the status, date and eligibility of the verified charge, without a confirm box.
- **Out of scope by subtype:** the reply says what is not possible and what is (loan, balance, card, address, transfer), then the advisor offer that already exists.
- **Slots ground the charge:** merchant words (fuzzy, accent-insensitive), amount, date phrase and "twice" match verified candidates; a slot that matches nothing is dropped. Code parsers read amounts in words and more date phrases as a fallback.
- **Why for a named charge:** grounds the charge and answers from the policy rule and its values.
- **Words:** in turns that do not decide, the reply shows the model draft only if the validator of `router-v3` accepts it, with verified values in the placeholders (decision 024). Otherwise, one of two or three reviewed template variants, picked by turn count. Decision turns always use templates.
- **Contract:** the reply adds an optional `text` beside `message_key`; the page shows `text` when present.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `chat`: openers, charge status, out-of-scope subtypes, slot grounding, why for a named charge, validated words.

## Impact

- `sentinel-ai-core/app/orchestrator/step.py`, `app/ai/grounding.py`, `app/orchestrator/explanation.py`, `app/schemas/chat.py`, `app/routers/demo_chat.py`, locale files, `static/app.js` (read `text` only), tests, [conversation rules](../../../docs/build/conversation.md).
- Merges after `flow-fixes`. `router-v3` measures the result in `eval-v8`.

## Non-goals

- Model words in turns that decide.
- Changes to the keyword baseline.
- Balances or any second flow (decision 008).
