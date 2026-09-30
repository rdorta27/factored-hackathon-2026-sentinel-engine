# Design: refine-mvp-gold-layer-proof-of-work

## Context

See proposal.md (Why). Current state: `POST /chat` creates cases from mock-orchestrator keywords with fixed facts (`ACME Store`, `2026-09-20`); `CaseConfirmation` carries facts plus `verified=true` but no policy check, no hold, no SLA, no receipt. Decision 003 already fixes the 90-day window as synthetic configurable policy with a simulated demo "today". Constraints: same stack, no new runtime libs, work inside `sentinel-login/`.

## Goals / Non-Goals

**Goals:**

- One policy gate (`DisputeService`) used by both the HTTP endpoint and the chat flow, so there is exactly one place where "eligible" is decided.
- Gold seam that Phase 2 (DuckDB/Delta) implements without touching callers.

**Non-Goals:**

- Real lakehouse wiring, real CRM calls, and real money holds stay out; the hold is a case status string.

## Decisions

- **Endpoint plus service, chat calls the service.** `POST /api/v1/disputes/create` is a thin HTTP skin over `DisputeService.create(...)`; the chat endpoint calls the same service function in-process (no self-HTTP). One policy implementation, two entries. Alternative rejected: duplicating eligibility logic in the chat layer.
- **Eligibility as pure function of (row, policy, demo-today).** `check_eligibility(row, policy) -> ok | reason` with policy (`window_days=90`, article reference) injected from configuration, and "today" as a parameter defaulting to the simulated demo date per decision 003. Testable without clocks; per-country values later. Alternative rejected: hardcoding 90 days in the endpoint.
- **Idempotency keys stored beside cases.** `Idempotency-Key` header (fallback: generated per chat turn) maps to the returned payload; repeat delivery returns the stored result. The chat turn id doubles as the key so double-submits from the UI cannot double-create. Alternative rejected: trusting the frontend to de-duplicate.
- **Proof-of-Work extends the contract, kind unchanged.** `CaseConfirmation` gains `hold`, `eligibility` (rule plus article), `sla_deadline`, `receipt_ref`, `queue_status`; `kind` stays `case_confirmation` so the `chat` delta and existing tests keep holding. SLA deadline computed as creation plus 24h on the simulated date. Alternative rejected: a new reply kind that would ripple through frontend and specs.
- **Gold mock seeded per demo customer.** `MockGoldStore` holds a handful of invented rows for `CUST-0001` covering the matrix: eligible recent charge, 120-day-old charge, refunded charge, already-disputed charge, and a foreign row owned by another id (invisibility test). Rows carry `as_of` = simulated date. Alternative rejected: reusing real dataset rows (repo rule forbids data).
- **Receipt as reference, download as endpoint.** `receipt_ref` like `RCPT-CASE-0001`; `GET /api/v1/disputes/{id}/receipt` returns a plain-text receipt (no new libs, no PDF). The frontend renders a download link. Alternative rejected: PDF generation (new dependency for a mock).
- **No new dependencies.** Dataclasses plus Pydantic; DuckDB arrives in Phase 2.

## Risks / Trade-offs

- [Risk] Chat behavior changes under the hood (facts now from Gold mock) → Mitigation: existing chat tests re-seeded against mock rows; scenario keywords kept stable.
- [Risk] Simulated hold could read as real → Mitigation: receipt and UI label it simulated/temporary; REQ-0004 named in the payload docs.
- [Risk] Simulated "today" vs real clock confusion → Mitigation: single `demo_today` config value, surfaced in the receipt; decision 003 already mandates this.
- [Risk] Scope touches chat, contract, frontend, plus two new modules → Mitigation: task order builds service plus tests first, chat rewire second, UI last.

## Migration Plan

1. Land Gold mock plus disputes service with tests; chat still on old path.
2. Rewire chat to the service; extend contract and card; full suite green.
3. Phase 2 swaps `MockGoldStore` for DuckDB/Delta adapters; endpoint, contract, and UI unchanged.
4. Rollback: revert chat rewire; endpoint can stay mounted unused.

## Open Questions

- None that change specs or tasks. The exact policy article number is a placeholder (`Art. 4`) until Natalia confirms the source (team task "Where does the 90-day dispute window come from").
