# Proposal

## Why

The charge-inquiry loop keeps conversational context it never enforces: `clarification_count` grows without a stop rule, denied charges can be shown again, corrections do not re-anchor, and the model only sees raw customer turns. Closing these gaps wins REQ-0001 and makes clarification, escalation, and retention demonstrable. See `docs/requirements/requirements.md` (REQ-0001) and decisions 005, 007, 008.

## What Changes

- Cap clarifications at 2: the third vague turn returns `handoff` with `fields.missing` (forced in `step.py`, policy files untouched).
- Add `rejected_ids` to `ConversationState`; denied or superseded candidates are excluded from the next ranking; a correction with amount/date re-anchors to the repaired candidate.
- Pass a deterministic digest (last 2 system questions + shown candidate ids) alongside the 4-turn window to `ModelPort.understand` via an optional `context` argument; `DemoModel`/`FakeModel` ignore it.
- Derive an explicit `Phase` (`COLLECTING`, `CLARIFYING`, `AWAITING_CONFIRMATION`, `RESOLVED`, `HANDED_OFF`) from state plus turn outcome; expose it on the handoff package and turn record.
- Bound `history` (50) and `actions` (200) per session with an `overflow` mark; language persists across turns including an es-419 to pt-BR switch.
- Replace the negative `fields.missing` assertion in `tests/test_chat.py` with six positive conversational tests.

## Capabilities

### New Capabilities

- None. All behavior refines existing capabilities.

### Modified Capabilities

- `orchestrator-loop`: bounded clarification rounds, `rejected_ids` plus repair re-anchoring, derived phase.
- `chat`: third clarification becomes `handoff`, denied charges are filtered, bounded history/actions with overflow mark.
- `llm-router`: `understand` accepts an optional deterministic digest next to the turn window.
- `session`: conversation retention is bounded per session and still deleted on logout/expiry.

## Impact

Code: `sentinel-ai-core/app/orchestrator/step.py`, `types.py`, `app/ai/port.py`, `app/ai/llm.py`, `app/routers/demo_chat.py`, `app/state/conversation.py`; tests `test_chat.py`, `test_ai_router.py` plus new conversational tests. No contract change for `DemoModel`/`FakeModel`; no policy YAML change; no data/ML or delivery impact.

## Non-goals

No change to policy thresholds or country files (REQ-0007, decisions 025/026/027 stay open); no data pipeline or model-training work (REQ-0015/0016/0019/0020); no delivery work (REQ-0035/0036/0037); no new locales beyond es-419 and pt-BR; no chain-of-thought in the digest.
