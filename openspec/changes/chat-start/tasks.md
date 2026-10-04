---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [008](../../../docs/build/decisions/008-account-inquiry-scope.md), [020](../../../docs/build/decisions/020-req-0001-context-tradeoffs.md). Plan: [chat behaviour](../../../team/chat-behavior-plan.md). Paths are under `sentinel-ai-core/`. Run `python3 -m pytest -q` after each group. Merge `flow-fixes` first.

## 1. Tests first

- [ ] 1.1 Write failing tests for: greeting, thanks, goodbye, "are you a bot", greeting plus request, charge status, why for a named charge, amounts in words, wording variants. Evidence: `tests/test_chat_start.py`.

## 2. Behavior

- [ ] 2.1 Add the opener subtypes on `missing` with replies in es-419 and pt-BR. Evidence: tests.
- [ ] 2.2 Answer a `status` label from the verified candidate without the box. Evidence: tests with a fake router that returns `status`.
- [ ] 2.3 Answer why for a named charge through the explanation module. Evidence: the "enero" test.
- [ ] 2.4 Parse amounts in words and more date phrases in `app/ai/grounding.py`. Evidence: the "mil pesos" test finds the 1,000 charge.
- [ ] 2.5 Add reviewed wording variants per key and a deterministic pick. Evidence: locale files and a test that a replay gives the same text.

## 3. Evidence

- [ ] 3.1 Run the adversarial suite and `eval.run verify 2024Q4-resolution-v2`; freeze a new resolution run if needed. Evidence: new runs and the verify output.
- [ ] 3.2 Update the conversation rules and the manual tests. Evidence: `docs/build/conversation.md`, `team/chat-manual-tests.md`.
