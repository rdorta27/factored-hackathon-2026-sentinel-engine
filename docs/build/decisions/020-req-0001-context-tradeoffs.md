---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 020 · Conversational context trade-offs for REQ-0001

**Date:** 2026-10-02
**Status:** Accepted
**Participants:** Team

## Context

The charge-inquiry loop kept conversational context, but it did not use it (REQ-0001):

- `clarification_count` grew with no stop rule.
- The loop could show denied charges again.
- A correction did not re-anchor the conversation.
- The model saw only raw customer turns.

The fix had to stay deterministic and free of cost. It also had to make clarification, escalation and retention visible in a demo (REQ-0002, REQ-0006, REQ-0027).

## Options

1. **Cap clarifications at 2 in `step.py` and force `HANDOFF fields.missing`.** The smallest change. It leaves the unused policy rule (`mandatory_fields: []` in all country files) as it is. Against: the audit trail cites a rule that the policy files do not define.
2. **Use the policy rule again: fill `mandatory_fields` in the MX, CO and AR files.** Consistent with the engine. It extends the change to three country files and to every test that checks them.
3. **Send the full system transcript to the model.** The most context. It makes the prompt larger and can carry customer words that the PII guard must check.
4. **Keep a small history and action list (20 turns).** The simplest retention story. Long advisor tickets lose the middle of the conversation.

## Decision

- Option 1 for the stop rule.
- Instead of option 3: a deterministic digest (`sys_questions` and `shown_ids`), with no customer words and no chain-of-thought.
- Instead of option 4: `history 50 / actions 200`, with an `overflow` mark.
- Denied or replaced charges go into one `rejected_ids` list. There is no separate `replaced` field.
- The loop derives the phase. It never stores it.

## Consequences

- Gain: a stop rule that a demo can show, a ranking with no repeats, re-anchoring after a correction, and bounded retention. `tests/test_conversational_context.py` covers all of them.
- Cost: the `fields.missing` citation comes from code, not from the policy files. The escalate record shows this difference.
- Open: the 4-turn window and the digest are a heuristic, not a measured optimum. *Updated 10/4:* the policy thresholds of pending decisions 25, 26 and 27 are closed by [010](010-fraud-handoff-rule.md), [011](011-high-amount-threshold.md) and [014](014-data-staleness.md).
