# 020 · Conversational context trade-offs for REQ-0001

**Date:** 2026-10-02
**Status:** Accepted
**Participants:** Team

## Context

The charge-inquiry loop kept conversational context it never enforced: `clarification_count` grew without a stop rule, denied charges could be shown again, corrections did not re-anchor, and the model only saw raw customer turns (REQ-0001). The fix had to stay deterministic and cost-free while making clarification, escalation, and retention demonstrable (REQ-0002, REQ-0006, REQ-0027).

## Options

1. **Cap clarifications at 2 in `step.py`, forcing `HANDOFF fields.missing`.** Smallest blast radius; leaves the dead policy rule (`mandatory_fields: []` in all country files) untouched. Con: the audit trail cites a rule the policy files do not define.
2. **Relive the policy rule by filling `mandatory_fields` in the MX/CO/AR files.** Consistent with the engine, but widens the change to three country files and every test that asserts on them.
3. **Pass the full system transcript to the model.** Richest context, but leaks toward prompt bloat and risks carrying customer words the PII guard reasons about.
4. **Bound history/actions aggressively (20 turns).** Cheapest retention story, but long advisor tickets lose the middle of the conversation.

## Decision

Option 1 for the stop rule; a deterministic digest (`sys_questions` plus `shown_ids`, no customer words, no chain-of-thought) instead of option 3; `history 50 / actions 200` with an `overflow` mark instead of option 4. Denied or superseded charges join one `rejected_ids` list (no separate `replaced` field); the phase is derived, never stored.

## Consequences

- We gain: a demonstrable stop rule, no-repeat ranking, repair re-anchoring, and bounded retention, all covered by `tests/test_conversational_context.py`.
- We sacrifice: the `fields.missing` citation now comes from code, not from the policy files; the divergence is recorded on the escalate record and stays visible.
- Pending: policy thresholds and country files are unchanged (decisions 025/026/027 stay open); the 4-turn window plus digest remains a heuristic, not a measured optimum.
