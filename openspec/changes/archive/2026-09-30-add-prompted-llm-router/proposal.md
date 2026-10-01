# Proposal

## Why

The loop classifies intent, language and the charge through `ModelPort`, but the
only implementation is `DemoModel`, a keyword stand-in; there is no router and no
real model call. The hybrid LLM router of decision 010 does not exist, and
REQ-0019 and REQ-0055 cannot be measured because the model identity and token
cost are never produced. The evaluation runner needs a real prompted LLM behind
the same contract before any learned-component comparison (REQ-0016) is possible.

## What Changes

- Add a prompted LLM router implementing `ModelPort.understand` against an
  OpenAI-compatible endpoint, with a model chosen per route (a cheaper model for
  frequent turns, a stronger one for ambiguous or Portuguese turns), per
  decision 010.
- Keep `DemoModel` as the keyword baseline behind the same port.
- Add a model seam (`create_app(model=...)` and `app.state.model`) replacing the
  `chat._MODEL` module global, so the process runs with either implementation.
- Expose model identity through `describe()` (model, route, prompt_version) and
  emit real `model`, `route`, `prompt_version`, `tokens_in`, `tokens_out` and
  `cost_usd` on the `understand` record (REQ-0019, REQ-0055).
- Align the router prompt and its extraction schema with the Gold service
  contract (`ServiceDisputeEligibleTransaction`): contract field names, numeric
  types, and no PII columns reaching the model (REQ-0047).
- Support recorded fixtures so tests and the runner run offline and reproducibly.

## Non-goals

- The dispute-category classifier (`ModelPort.classify`) and its baseline
  comparison: separate change.
- The evaluation cases, metrics and runner: separate change.
- Policy, eligibility and confirmation logic: unchanged; the router never decides
  permissions (REQ-0007).
- Choosing the production model or provider: decision 010 stays open; the client
  stays provider-agnostic.

## Capabilities

### New Capabilities

- `llm-router`: routes each understand call to a model, returns intent and
  language, reports its model and prompt identity, and never sees PII.

### Modified Capabilities

None.

## Impact

- Code: `sentinel-ai-core/app/ai/` (new `llm.py`; keep `demo.py` and `fake.py`),
  `app/main.py`, `app/routers/chat.py`, `app/orchestrator/step.py` (emit model
  identity).
- Tests: new offline tests over recorded fixtures; existing tests keep passing
  with `DemoModel`.
- Config: `.env.example` gains LLM provider and model variables; no secrets in
  the repository.
- Requirements: REQ-0001, REQ-0012, REQ-0019, REQ-0047, REQ-0055; decisions 005,
  007, 010.
