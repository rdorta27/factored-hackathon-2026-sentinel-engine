# Tasks

## 1. Record schema and writer

- [x] 1.1 Create `app/observability/records.py` with the step/turn record dataclass, JSON serialization, and constructor-level PII guards; verify with a unit test that forbids customer text, identifiers, tokens, and IPs (evidence: `sentinel-ai-core/tests/test_observability.py::test_record_rejects_pii`; see `docs/build/decisions/004-pii-lifecycle.md`)
- [x] 1.2 Create `app/observability/writer.py` with the dual sink (in-memory list plus JSONL append at a configurable path, default `var/turns.jsonl`) and salt handling (`SENTINEL_SESSION_SALT`, ephemeral plus warning when unset); verify records round-trip through both sinks in a unit test (evidence: same file; see `docs/build/areas/ai.md`)
- [ ] 1.3 Add `var/` to `.gitignore` and document `SENTINEL_SESSION_SALT` plus `SENTINEL_REFERENCE_DATE` in a new `.env.example` with no real values; verify `git check-ignore var/` passes and no secret lands in the repo (evidence: `.env.example`, `git status`; see `docs/architecture/specification.md`, Data retention section)

## 2. Loop and chat wiring

- [ ] 2.1 Extend `Ports` with optional `trace_id` and observer fields defaulting to no-op and emit one record per loop step from `step()` with policy rule, tool outcome, attempt, and latency; verify existing orchestrator tests still pass unchanged (evidence: `python3 -m pytest sentinel-ai-core/tests/test_demo_cases.py sentinel-ai-core/tests/test_policy_gate.py -q`; see `docs/build/decisions/007-learned-component.md`)
- [ ] 2.2 Wire a per-turn recorder in `POST /chat` reusing the middleware `trace_id`, emitting the closing record with final outcome and aggregates including the exception and unknown-charge paths; verify a text turn and a failing turn each leave a complete trace (evidence: new tests in `tests/test_observability.py`; see `docs/build/areas/ai.md`)

## 3. Session audit migration

- [ ] 3.1 Migrate `AuditLogger` to emit `step: session` records through the shared writer with salted `session_ref` and no IP, updating `service.py` and `router.py` call sites; verify the session suite passes on the new shape (evidence: `python3 -m pytest sentinel-ai-core/tests/test_session.py -q`; see `docs/build/decisions/008-pii-gold-handling.md`)
- [ ] 3.2 Map the raw Gold status through the candidate adapter in `GET /transactions` and unmark the 2 strict xfail tests; verify the full service suite is green (evidence: `python3 -m pytest sentinel-ai-core/tests/ -q`; see `docs/build/areas/ai.md`)

## 4. Acceptance and traceability

- [ ] 4.1 Add the end-to-end acceptance test (login, chat, confirm box, confirmation to `case_number`) asserting a single `trace_id`, zero PII by grep, numeric cost and latency with a non-null `decide` policy rule, and a file replay by `trace_id`; verify it passes (evidence: `tests/test_observability.py`; see `docs/architecture/specification.md`, Evaluation section)
- [ ] 4.2 Record REQ-0025 evidence in `docs/requirements/requirements.md` (stays In progress until the evaluation runner consumes the records) and mark the structured-logs row in `team/tasks.md`; verify the status counts recompute (evidence: requirements diff; see `docs/requirements/requirements.md`)
