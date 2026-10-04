---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [008](../../../docs/build/decisions/008-account-inquiry-scope.md), [020](../../../docs/build/decisions/020-req-0001-context-tradeoffs.md), 024 (in `router-v3`). Plan: [chat behaviour](../../../team/chat-behavior-plan.md). Paths are under `sentinel-ai-core/`. Starts after `flow-fixes` merges and contract v3 (task 1.1 of `router-v3`) is committed. Run `python3 -m pytest -q` after each group.

## 1. Tests first

- [ ] 1.1 Write failing tests with a fake router that returns contract v3: each opener subtype, greeting plus request, status, each out-of-scope subtype, each slot, why for a named charge, an accepted and a rejected draft, a decision turn that ignores the draft. Add the same cases with v2-style results for the fallbacks. Evidence: `tests/test_chat_start.py`.

## 2. Behavior

- [ ] 2.1 Openers by subtype, with the code fallback. Evidence: tests.
- [ ] 2.2 Charge status without a box. Evidence: tests.
- [ ] 2.3 Out-of-scope replies by subtype. Evidence: tests and locale keys in es-419 and pt-BR.
- [ ] 2.4 Slot grounding and the parser fallback for amounts in words and dates. Evidence: the "mil pesos" test.
- [ ] 2.5 Why for a named charge through the explanation module. Evidence: the "enero" test.
- [ ] 2.6 The words table, the optional `text` field and the template variants. Evidence: tests and the page shows `text`.

## 3. Evidence

- [ ] 3.1 Run the adversarial suite and `eval.run verify 2024Q4-resolution-v2`; freeze a new run if the change is intended. Evidence: new runs and the verify output.
- [ ] 3.2 Write `scripts/chat_transcripts.py`: about 40 scripted conversations (the phrases of Felix, openers, a loan request, amounts in words) in the four variants with the real model. It checks the expected kind and subtype, that no draft carries an unverified datum, the language, and that an opener never hands off. It writes the full conversations to a report, reusing `scripts/sentinel_client.py`. Evidence: the script and its report under `team/chat-manual-tests.md`.
- [ ] 3.3 Human review G2: the owner reads the report and asks for changes. Evidence: notes in `team/chat-manual-tests.md`.
- [ ] 3.4 Update the conversation rules. Evidence: `docs/build/conversation.md`.
