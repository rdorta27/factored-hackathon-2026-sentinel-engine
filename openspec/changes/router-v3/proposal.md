---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The router reads one of four labels, the language and the "not mine" claim. Everything else that the customer sees is a fixed template. The chat does not flow:

- "hola" gets "I can only help with charges".
- "quiero un préstamo" ("I want a loan") enters the dispute flow with the baseline (manual test of Felix, point 4).
- "un cobro de mil pesos" ("a charge of one thousand pesos") finds nothing (Felix, point 8).
- The sealed set of `2024Q4-eval-v7` has no opener, so its 0.98 says nothing about the first message.

The brief asks for an AI-first service, not a rigid bot. Diego (MLE at Factored) asks that every datum come from the source, not from the model. Both can be true: the model reads more and writes the words, and the code decides and writes the facts.

## What Changes

- **Contract v3** of `UnderstandResult`, fixed first: `kind` (`charge`, `status`, `missing`, `out_of_scope`, `person`), `subtype` (opener and out-of-scope kinds), `language`, `not_mine`, `slots` (merchant words, numeric amount, date phrase, "twice"), optional `reply_draft` with placeholders, `confidence`. The baseline fills only `kind` and `language`, and does not change.
- **Decision 024:** the model writes the words of turns that do not decide (openers, clarifications, out-of-scope explanations). Code inserts the verified values in placeholders. A validator rejects a draft with a figure, a name, a date or a promise that is not in the verified facts, a wrong language or a length over the limit. A rejected draft falls back to the template. Turns that decide (confirm box, case number, policy refusal, handoff) always use templates.
- **Prompt v3:** each intent and subtype defined in one line, each slot defined, development examples only, served behind `SENTINEL_LLM_PROMPT_VERSION=v3`. Cut-offs re-fitted on v3.
- **Development cases** for openers, status, subtypes and slots, in four variants.
- **One measurement, `2024Q4-eval-v8`:** baseline, the trained baseline of [`trained-baseline`](../trained-baseline/proposal.md), v2, v2 with cut-offs, v3, v3 with cut-offs, under the 018 amendment, with new metrics: subtype accuracy, slot precision, unnecessary-handoff rate, system outcome match, rejected-draft rate, and **unsafe wording** (a shown text with an unverified datum) counted as an unsafe outcome. The best candidate that passes every gate is served; otherwise v2 stays.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `llm-router`: contract v3, prompt v3, the draft validator, serving after v8.
- `sealed-case-set`: a second sealed set with openers, subtypes, slots and multi-turn resolution.

## Impact

- `sentinel-ai-core/app/ai/port.py`, `llm.py`, `serving.py`, a new `app/ai/drafts.py`, `eval/` (cases, examples, metrics, seal), decisions 007, 016, 018 and a new 024, the metrics report.
- [`chat-start`](../chat-start/proposal.md) consumes the contract. The seal waits for `flow-fixes`, `chat-start` and `trained-baseline` and for the human review of the chat.

## Non-goals

- The model decides nothing: no permission, eligibility, confirmation or handoff.
- Changes to the keyword baseline.
- Free text in turns that decide.
