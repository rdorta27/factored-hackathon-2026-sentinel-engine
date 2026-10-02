# Design

## Context

See proposal.md Why. Current state (verified in `main`): `clarification_count` increments in `app/orchestrator/step.py` but the only consumer (`policy/engine.py` `fields.missing`) is dead because all country files set `mandatory_fields: []`; `ConversationState` has no denied-id memory; `states_not_theirs` is a sticky bool; the model sees only the last 4 raw customer turns (`app/ai/llm.py` `build_messages`); `history`/`actions` append unbounded in `app/routers/demo_chat.py` `finish_turn`; state serializes via `asdict`/`_dump`/`_load`/`from_json` in `app/state/conversation.py` with no migration framework. Base for this change is `main` (`1740222`), isolated in worktree `.worktrees/req-0001-context`.

## Goals / Non-Goals

**Goals:**
- Enforce the clarification stop rule deterministically with zero model cost.
- Make denial and correction memory structural (`rejected_ids` + repair re-anchor).
- Give the model the missing system-side context without leaking PII or adding chain-of-thought.
- Name the conversation phase without duplicating state.

**Non-Goals:**
- No policy threshold or YAML change; no new locales; no CoT or prompt-version bump beyond the digest field.

## Decisions

- **Stop rule in `step.py`, not in policy files.** Guard at the top of the missing/grounding-failure branches: `clarification_count >= 2` returns `HANDOFF fields.missing` with an `escalate` emit. Alternative (fill `mandatory_fields` in YAMLs) rejected: it would relive a dead rule across three countries and widen the blast radius; the user confirmed forcing in code.
- **`rejected_ids: list[str]` on `ConversationState`, old ids appended, never a separate `replaced` field.** Denial appends the shown id; repair appends the superseded id and selects the new match. Ranking filters `rejected_ids` before the top-4 cut in `demo_chat.py`. Alternative (separate `replaced_ids`) rejected per user: one list is enough to guarantee "never shown again".
- **Digest as optional `context` on `ModelPort.understand`.** Shape `{"sys_questions": last 2 codes, "shown_ids": [...]}` built in `step.py`, serialized in `llm.py` next to `turns`. Signature stays backward compatible (`context=None`); `DemoModel`/`FakeModel` ignore it so the baseline suite is unaffected. Contract test first. Alternative (extend `turns` with system strings) rejected: it would pollute the customer-turn window the PII guard reasons about.
- **Derived `Phase` enum, exposed but not stored.** Pure `phase_of(state, last_output)`; written onto the handoff package and turn record only. No column migration since `state` is a TEXT JSON blob with tolerant `from_json` defaults.
- **Bounded retention `history 50 / actions 200` with `overflow` mark.** Oldest-first discard in `finish_turn`. Constants live next to the router; values documented as trade-offs (decision 0056). Alternative (20-turn aggressive cap) rejected per user.

## Risks / Trade-offs

- [Forcing `fields.missing` from code while YAMLs stay empty] → Mitigation: emit `policy_rule="fields.missing"` on the escalate record so the audit trail stays citable; document the divergence in the decision log.
- [Digest changes the prompted-router request shape] → Mitigation: optional arg, contract test asserting old two-arg calls still work, replay fixtures unaffected.
- [Repair vs. denial ambiguity when a correction matches nothing] → Mitigation: fall back to the normal clarification path and do not append to `rejected_ids`.
- [History truncation loses advisor context on very long sessions] → Mitigation: `overflow` mark plus phase and last verified charge still handed over.

## Migration Plan

No migration: new fields default (`rejected_ids=[]`, `overflow` absent) in `from_json`/`_load`; old rows load cleanly. Rollback is a code revert with no data repair. Deploy with the existing suite plus the six new conversational tests; no evidence rewrite (runs are write-once).
