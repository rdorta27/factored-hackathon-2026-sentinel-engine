# Proposal: refine-mvp-gold-layer-proof-of-work

## Why

The demo loop works but the MVP story is blurry: case creation lives inside the chat endpoint with fixed mock facts, no policy gate, and no Gold reads. This change sharpens the MVP around one golden rule (AI converses, code verifies and executes) and turns the confirmation into a Proof-of-Work card that answers the mentor's anxiety test: visible hold, verified rule, SLA clock, receipt, and queue status.

## What Changes

- Golden rule recorded as the architecture invariant: the LLM handles regional conversation, empathy, and intent extraction; all banking policy and state changes run deterministically in backend code. No SQL from the LLM, no writes to the lakehouse.
- Gold layer documented as a mock in Phase 1: a `GoldTransactions` protocol serving denormalized transaction rows (date, status, refunded and prior-dispute flags, as-of mark) from an invented in-memory seed; DuckDB locally and Delta Lake on Databricks in Phase 2 without contract changes.
- New endpoint `POST /api/v1/disputes/create` (role `customer`): takes a transaction reference plus an idempotency key, checks eligibility in code (within the 90-day window per `docs/build/decisions/003-disputes-flow.md`, not refunded or reversed, no prior dispute), creates the case, re-reads it, and returns the Proof-of-Work payload. Retries on transient failure are idempotent; ineligible transactions get a reason plus handoff, never a case.
- `POST /chat` delegates case creation to the disputes service (same process in Phase 1) instead of inventing facts; the mock orchestrator supplies intent only.
- The `case_confirmation` variant grows the five Proof-of-Work elements: temporary amount hold, verified eligibility rule (policy article), SLA deadline (24h from creation against the simulated demo date), downloadable receipt reference, and human-queue status. The frontend card renders all five.

## Capabilities

### New Capabilities

- `disputes`: dispute creation endpoint, deterministic eligibility policy, idempotent retries, Proof-of-Work payload.
- `gold-layer`: Gold read seam with eligibility fields, as-of freshness mark, and mock-vs-real documentation.

### Modified Capabilities

- None (no archived specs exist yet; the `chat` delta stays valid since the response variant keeps its kind).

## Impact

- New code in `sentinel-login/` (`app/disputes/`, `app/gold/`); `POST /chat` internals change but its contract and the five reply kinds do not.
- New endpoint `POST /api/v1/disputes/create`; no new runtime dependencies.
- Frontend receipt card extended with the five Proof-of-Work elements.
- Traces to REQ-0003, REQ-0004, REQ-0005, REQ-0006, REQ-0008, REQ-0026, REQ-0033, REQ-0039, REQ-0043, REQ-0048; builds on `docs/build/security.md`, `docs/build/architecture-roadmap.md`, and decisions 003/005/006.

## Non-goals

- Real DuckDB/Delta wiring, the real orchestrator, and real CRM integration stay Phase 2; only the seams and mock adapters land here.
- No real money movement: the "hold" is a simulated status on the mock case (REQ-0004).
- No dashboard, no multi-worker stores, no new locales or themes.
