---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Context

Prompt v2 (`app/ai/llm.py`) lists four intents without definitions, asks for an `amount` that the code ignores, and has eight development examples, none an opener. Replies carry translation keys only (`app/schemas/chat.py`). The runner seals by hash, refuses a second measurement of a hash, and freezes runs write-once. The app serves v2 and fails at startup if its examples do not load.

## Decisions

1. **Contract first.** `UnderstandResult` v3 is the interface for `chat-start`, the isolated author of the sealed set, and `trained-baseline`. It is fixed and committed before prompt work. New fields are optional, so v1, v2 and the baseline still fit.
2. **Status is a model label; dispute status is code.** A question about the status of a charge is `status`. A question about an existing dispute stays the code check of `flow-fixes`, so it works with any model.
3. **Subtypes instead of new intents.** Greetings stay `missing` with a subtype; a loan stays `out_of_scope` with a subtype. The intent block of v7 stays comparable.
4. **Slots are hints, not facts.** Code matches each slot against verified candidates; a slot that matches nothing is dropped. A wrong slot cannot select a charge.
5. **Drafts with placeholders (decision 024).** The model never writes a value. The validator (`app/ai/drafts.py`) checks for digits outside placeholders, unknown placeholders, names and dates not in the facts, promise words, language and length. Rejections are logged as `draft_rejected` with a reason.
6. **Amendment before numbers.** It extends the 018 amendment of `router-confidence`. It keeps every v7 gate, adds the new metrics, sets targets from development numbers, and fixes the spend cap.
7. **Two authoring steps.** The isolated author writes the intent block as soon as the contract is fixed, and the multi-turn block after the human review of the chat, when the behavior is fixed.
8. **Same settings as v7.** GLM 5.3 Flash on both routes, reasoning low, temperature 0, same seed; the token cap may rise for the draft and is reported.

## Risks / Trade-offs

- **Time:** the full measurement is long. The multi-turn block is the first cut.
- **Injection through the draft:** covered by the validator, adversarial tests and the unsafe-wording metric.
- **Latency and cost:** a longer prompt and a draft cost more; both are reported beside v7.
- **Model-written cases:** the same provenance limit as v7; stated.
