# Proposal

## Why

A customer whose charge is refused cannot ask why. After "Hay un cobro de 2500 MXN en ACME Store" the chat correctly says the charge is outside the dispute window, but the follow-up "¿en qué te basas, de dónde salen los 90 días?" is read as a new message and returns the generic charge list (manual test MT-05). Explainability of a decision made in code is part of REQ-0033 and a visible weakness in the demo, and the safety rules (high amount, fraud) need a defined answer that does not reveal their criteria.

## What Changes

- The conversation keeps the **last policy decision** per thread: `rule_id`, the candidate and a snapshot of the verified values it used.
- A **why follow-up** is recognised deterministically, only when a last decision exists. It answers from that stored decision and does not recompute it.
- The answer is a new structured reply carrying a translation key and verified values (rule, `window_days`, charge date, last eligible date, whether the policy is a demonstration). The model writes none of it ([007](../../../docs/build/decisions/007-learned-component.md)).
- **Window and status rules** (`window.expired`, `status.pending`, `status.reversed`, `status.declined`, `already.disputed`) explain their rule and values. The window number is read from `window_days`, never from a text.
- **Safety rules** (`amount.high`, `fraud.score`, `fraud.claim`) answer with one fixed sentence that names no threshold, score or the word fraud ([010](../../../docs/build/decisions/010-fraud-handoff-rule.md), [011](../../../docs/build/decisions/011-high-amount-threshold.md)).
- With no stored decision, the answer says what the service can do and invents no rule.
- The adversarial set gains probing attempts, still expected at 0 unsafe outcomes.
- README and slide wording that justifies what was left out ([021](../../../docs/build/decisions/021-dispute-policy-sources.md)).

## Capabilities

### New Capabilities
- `decision-explanation`: what the service remembers about its last decision, how a why follow-up is recognised, and what each rule may and may not disclose.

### Modified Capabilities
- `chat`: a new structured reply variant for an explanation, and the rule that a why follow-up is not treated as a new charge request.

## Impact

- Code in `sentinel-ai-core/`: orchestrator state and step, conversation JSON (backward compatible), chat schema, `demo_chat.py`, locale files, the page.
- Tests, plus new attacks; adversarial evidence is produced by the suite.
- Requirements: REQ-0033 (strengthened), REQ-0006, REQ-0030. None created for the real-policy work.
- Not changed: router and prompt, `eval-v7`, policy files and values, Gold.

## Non-goals

- Real windows, window start by country, bank obligations and Visa or Mastercard rules per card: production path in [021](../../../docs/build/decisions/021-dispute-policy-sources.md).
- Greeting handling stays with prompt v3 so `eval-v8` measures it ([plan](../../../team/router-v3-plan.md)). Until then a greeting gets the out-of-scope offer, never a ticket.
- Charge narrowing from merchant, amount or date, model-written wording and by-conversation evaluation: later work.

## Assumptions

- Greetings are not handled in code (option B of the exploration), to keep `eval-v8` meaningful.
- The set of explanation kinds is small and lives in code keyed by `rule_id`; country files keep only values, so a bank changes a value without touching code.
