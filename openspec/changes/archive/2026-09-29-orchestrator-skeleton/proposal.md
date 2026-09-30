# Proposal

## Why

The dispute flow has no loop yet. The skeleton must run Understand → Decide → Act → Verify → Escalate in code, so a charge inquiry becomes a dispute only when policy allows it, and a case number is reported only after a read-back (REQ-0005, REQ-0009). Decision 005 defers LangGraph and requires the thinnest loop that meets the contracts.

## What Changes

- Add a plain-Python turn function in `sentinel-ai-core/app/orchestrator/`: `step(turn, state, ports)`.
- Keep conversation state across turns: shown candidates, pending confirmation, detected language (`es-419` or `pt-BR`), and clarification count (REQ-0001).
- Evaluate closed policy rules in `app/policy/` before any learned component or model wording (REQ-0007, REQ-0048, decision 008).
- Confirm state-changing actions with a single-use `confirmation_token` and an idempotency key, then read the dispute back with a bounded retry (REQ-0006, REQ-0026).
- Drive the three demo cases with a fake model port, in `es-419` and `pt-BR` (REQ-0009, REQ-0010, REQ-0011).

## Capabilities

### New Capabilities

- `orchestrator-loop`: one turn over conversation state; text or a structured candidate id in, a question, confirm box, case number, handoff, or failure out.
- `dispute-confirmation`: token, idempotency key, and read-back before a case number.
- `decision-priority`: policy outcome is final; the learned component only fills the dispute category; the model never confirms or chooses the customer.

### Modified Capabilities

- None. No specs exist yet.

## Impact

- New package `sentinel-ai-core/` with `app/orchestrator/`, `app/policy/`, and a tool port plus in-memory fakes under `app/tools/`.
- No HTTP route, chat page, session store, Gold read, or real model in this change.
- Callers pass session-bound tools. The loop does not receive `customer_id` (decision 005, REQ-0047).

## Non-goals

- LangGraph, or a second process for the loop (decision 005).
- Fraud and high-amount thresholds (pending decisions 25 and 26). Without a threshold, that rule does not exist.
- The real dispute-category classifier and its held-out set (decision 007). This change only defines the port.
- Hard-coding one subcategory. *Cargo no reconocido* (unrecognized charge) is the documented example, not the only path.
