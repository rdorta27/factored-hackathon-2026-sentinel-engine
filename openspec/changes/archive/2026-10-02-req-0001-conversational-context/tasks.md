# Tasks

## 1. Contract and stop rule

- [x] 1.1 Add ModelPort contract test for optional digest and verify `python -m pytest tests/test_ai_router.py -q` passes; evidence `sentinel-ai-core/tests/test_ai_router.py`; see `docs/build/areas/ai.md`.
- [x] 1.2 Enforce max 2 clarification rounds with `HANDOFF fields.missing` in `step.py` and verify the third vague turn hands off; evidence `sentinel-ai-core/tests/test_chat.py`; see `docs/build/decisions/008-*` (flow selection) via `docs/build/areas/ai.md`.
- [x] 1.3 Replace the negative `fields.missing` assertion with the positive third-round handoff test and verify `python -m pytest tests/test_chat.py -q` passes; evidence `sentinel-ai-core/tests/test_chat.py`; see `docs/build/areas/ai.md`.

## 2. Denial memory and repair

- [x] 2.1 Add `rejected_ids` to `ConversationState` with `_dump`/`_load`/`from_json` persistence and verify old rows load as `[]` via `tests/test_state_sqlite.py`; evidence `sentinel-ai-core/app/orchestrator/types.py`; see `docs/build/areas/ai.md`.
- [x] 2.2 Filter `rejected_ids` from the clarification ranking and append on denial, then verify a denied charge never reappears; evidence `sentinel-ai-core/tests/test_chat.py`; see `docs/build/decisions/005-backend.md`.
- [x] 2.3 Implement amount/date repair re-anchoring with the superseded id appended to `rejected_ids` and verify the repaired candidate wins; evidence `sentinel-ai-core/tests/test_grounding.py`; see `docs/build/areas/ai.md`.

## 3. Model context digest

- [x] 3.1 Build the deterministic digest (last 2 system questions + shown ids) in `step.py` and verify it carries no PII via the contract test; evidence `sentinel-ai-core/app/ai/llm.py`; see `docs/build/decisions/007-learned-component.md`.
- [x] 3.2 Thread the digest through `build_messages` keeping two-arg calls working and verify `DemoModel`/`FakeModel` behavior is unchanged; evidence `sentinel-ai-core/tests/test_ai_router.py`; see `docs/build/areas/ai.md`.

## 4. Phase and bounded retention

- [x] 4.1 Add the derived `Phase` enum plus `phase_of` and expose it on the handoff package and turn record, verifying `CLARIFYING` on a question turn; evidence `sentinel-ai-core/app/orchestrator/types.py`; see `docs/build/decisions/005-backend.md`.
- [x] 4.2 Bound `history` to 50 and `actions` to 200 with oldest-first discard and an `overflow` mark, verifying the mark appears past the bound; evidence `sentinel-ai-core/app/routers/demo_chat.py`; see `docs/build/areas/analysis.md` (retention REQ-0027).

## 5. Conversational acceptance tests

- [x] 5.1 Add tests that the model receives prior turns, language persists across 4 turns and an es-419 to pt-BR switch, and verify the new test file passes; evidence `sentinel-ai-core/tests/test_conversational_context.py`; see `docs/build/areas/ai.md`.
- [x] 5.2 Document the 2-round cap and 4-turn window plus digest as trade-offs and verify the decision file renders; evidence `docs/build/decisions/0XX-req-0001-context-tradeoffs.md`; see `docs/build/decisions/007-learned-component.md`.

## 6. Integration check

- [x] 6.1 Run the affected suites `test_chat.py test_ai_router.py test_policy_engine.py test_state_sqlite.py` from `sentinel-ai-core/` and verify all pass with no policy YAML change; evidence pytest output pasted in the task commit body; see `docs/build/areas/ai.md`.
