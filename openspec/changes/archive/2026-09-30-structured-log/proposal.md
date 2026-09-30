# Proposal

## Why

The system is a black box: nobody can say how long a turn takes, what it costs, or which rule decided each case. Without that receipt there is no evaluation, no metrics for the slides, and no monitoring. The evaluation runner (which scores every case by reading logs) cannot be built until each turn leaves a structured, PII-free trace.

## What Changes

- New `app/observability/` package: `StepRecord` schema (the 16 fields of the architecture specification, Observability section) plus a `TurnRecord` closing line per turn (final outcome with aggregated cost and latency).
- Dual sink: in-memory list for tests plus a JSONL file the runner filters by `trace_id`.
- Wiring: one record per loop step from `step()` via extended `Ports` (`trace_id` and recorder as optional fields, `None` is a no-op); a closing record per `POST /chat` turn, including the exception path so failures stay measurable.
- **BREAKING** (internal): `AuditLogger` migrates to the record format as `step: session`; cleartext `customer_id` becomes a salted `session_ref` hash and the client IP is dropped. Tests reading `audit.records` move to the new shape in the same change.
- Drive-by fix: `GET /transactions` maps the raw Gold status through the candidate adapter (no more verbatim `Refunded`), fixing 2 strict xfail tests.
- New `.env.example` documenting `SENTINEL_SESSION_SALT` and `SENTINEL_REFERENCE_DATE` with no real values.

## Capabilities

### New Capabilities

- `observability`: per-step and per-turn structured records with `trace_id`, `session_ref`, tool/outcome/attempt, `policy_rule`, latency, model/route/prompt version, tokens, cost, language and country; dual sink; salt handling. Traces to REQ-0025, REQ-0029, REQ-0055, REQ-0019, REQ-0024, REQ-0050.

### Modified Capabilities

- `session`: the audit-record requirement changes from cleartext customer plus IP to the observability record format with salted `session_ref` and no IP. Traces to REQ-0047 and decision 004 (PII lifecycle). See `docs/build/decisions/004-pii-lifecycle.md` and `docs/build/decisions/008-pii-gold-handling.md`.

## Non-goals

Centralized logging, alerts, and dashboards (production, per the specification, Data retention section); an LLM judge; GoldRow format changes; `trace_id` in success payloads.

## Impact

New code in `sentinel-ai-core/app/observability/`; edits in `app/orchestrator/step.py` (`Ports` only), `app/routers/chat.py`, `app/routers/transactions.py`, `app/session/`; new `tests/test_observability.py`; `.env.example`; `.gitignore` gains `var/`. REQ-0025 stays In progress until the evaluation runner consumes the records.
