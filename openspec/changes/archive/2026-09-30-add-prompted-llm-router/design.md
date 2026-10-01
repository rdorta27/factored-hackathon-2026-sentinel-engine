# Design

## Context

See proposal.md for motivation. Current state that shapes the approach:

- `ModelPort` has one method used by the loop, `understand(message, turns)`, plus
  `classify(message)`; only `DemoModel` (keyword) and `FakeModel` (tests) exist.
- The loop calls `ports.model.understand` in `app/orchestrator/step.py`; the
  model is a module global `_MODEL` in `app/routers/chat.py`, so it cannot be
  swapped per run.
- The `understand` record already exists but emits the observer defaults
  `model="fake"`, `route="mock"`, `prompt_version="none"`, zero tokens and cost.
- The Gold service contract `ServiceDisputeEligibleTransaction`
  (`sentinel-data-engine/src/sentinel_data/schemas.py`) fixes numeric `amount`
  and `fraud_score` and drops three PII columns; the service seam still carries
  the older `GoldRow` shape.
- Decision 010 keeps the model per route open; the client must not hard-code a
  provider. The loop is synchronous and runs one model call per turn.

## Goals / Non-Goals

**Goals:**
- A real prompted LLM router behind `ModelPort.understand`, provider-agnostic and
  route-aware, with the keyword baseline kept.
- Real model identity, tokens and cost on the turn records.
- Reproducible offline runs through recorded responses.
- The prompt and extraction schema aligned to the Gold service contract, with no
  PII reaching the model.

**Non-Goals:**
- The dispute-category classifier (`classify`) and its comparison.
- The evaluation cases, metrics and runner.
- Choosing or deploying the production model (decision 010).
- Changing the loop's behavior, policy or confirmation.

## Decisions

### Decision: transport behind a protocol, HTTP by default

The model client sits behind a `ModelTransport` protocol with one method that
takes a request and returns the raw response. The default transport posts JSON to
an OpenAI-compatible endpoint with `httpx`; tests and the runner use a
`FixtureTransport` that replays committed responses. Alternatives: stdlib
`urllib` (rejected: weaker timeouts and retries), the unmerged AsyncAnthropic
branch (rejected: provider-specific and async while the loop is sync).

### Decision: route table with a cheap pre-check

Routes are named per call type and profile (for example a cheap route for short,
frequent turns and a strong route for ambiguous or Portuguese turns). A cheap
pre-check (language heuristic and message shape) picks the route before the
model call; an unknown route falls back to a configured default. The table lives
in configuration, not code, so decision 010 can be settled without touching the
loop. Alternative: a single model (rejected: loses the cost lever the brief
rewards).

### Decision: model seam at the app factory

`create_app(model=None)` stores the chosen model on `app.state.model`, defaulting
to the keyword baseline; `chat` reads it per request. The `_MODEL` global is
removed. This lets tests and the runner select the router or the baseline without
editing code.

### Decision: describe seam for identity

`ModelPort` gains `describe()` returning a small `ModelInfo(model, route,
prompt_version)`. The loop passes it to the observer so the `understand` record
carries real values, and tokens and cost flow back from the model result. The
keyword baseline returns its own non-empty identity with zero tokens and cost.

### Decision: recorded fixtures, deterministic by default

Responses are stored as committed JSON fixtures under
`sentinel-ai-core/app/ai/fixtures/`, keyed by `prompt_version` and a hash of the
normalized input, holding the understanding result and the token and cost
figures. Default sampling is deterministic (temperature 0) so a live run and a
replay match. Recording is one online run; each fixture is reviewed for personal
data before it is committed. The evaluation runner replays the same fixtures, so
its numbers are reproducible offline.

Test transports: the loop is exercised with `DemoModel` (no network), unit tests
of the router use a `StubTransport` (a canned response computed from the input),
and the router and the runner use a `FixtureTransport` that replays committed
responses and opens no connection.

### Decision: Gold-aligned, PII-free request

The request builder whitelists the fields the model may see (the message, the
bounded turn window, and charge fields named as in the service contract with
numeric types). A guard rejects any request containing a forbidden key
(`customer_id`, session token, or a PII column) before it leaves the process.

### Decision: bounded retry, typed failure

The transport retries a bounded number of times on timeout or 5xx and then raises
a typed `ModelUnavailable`. The loop treats it as a failure: safe fallback and
handoff, never an unverified answer.

## Risks / Trade-offs

- [Provider outage or cost spike] → bounded retry, safe fallback, and fixtures for
  offline runs; cost is recorded per turn.
- [PII leaks into the prompt] → request whitelist plus a guard test; the
  adversarial set already tracks the free-text path (`A9`).
- [Non-determinism breaks reproducibility] → deterministic default and recorded
  fixtures; the live model is used only when configured.
- [New runtime dependency] → `httpx` is already present transitively (TestClient);
  declare it explicitly in `sentinel-ai-core/pyproject.toml`.
- [Decision 010 still open] → the client is provider-agnostic and the route table
  is configuration, so no spec or task depends on the choice.

## Migration Plan

Additive. The keyword baseline stays the default, so nothing changes until
`SENTINEL_LLM_*` variables are set. Rollback is unsetting them (or passing the
baseline to `create_app`).

## Open Questions

- The exact providers, model ids and prices for each route (decision 010).
- The fixture file layout and whether fixtures are shared with the evaluation
  runner or kept per change.
