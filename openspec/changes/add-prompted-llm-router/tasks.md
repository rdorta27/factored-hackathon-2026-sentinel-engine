# Tasks

## 1. Model contract and seam

- [x] 1.1 Extend `ModelPort` with `describe()` returning `ModelInfo(model, route, prompt_version)`, and implement it on `DemoModel` and `FakeModel`; verify with a unit test asserting the baseline identity is non-empty (evidence: `sentinel-ai-core/tests/test_ai_router.py`; refs: `docs/build/areas/ml.md`, decision 007)
- [x] 1.2 Add `create_app(model=None)` storing `app.state.model` (default the keyword baseline) and read it in `app/routers/chat.py`; remove the `_MODEL` global; verify the existing `tests/test_chat.py` passes with the default and a test injects `FakeModel` (evidence: `sentinel-ai-core/app/main.py`, `tests/test_chat.py`; ref: decision 005)
- [x] 1.3 Document the seam and the `SENTINEL_LLM_*` variables in `sentinel-ai-core/README.md` and `.env.example`; verify the README lists each variable and the file holds no values (evidence: `.env.example`; ref: `docs/build/decisions/010-*` or `team/pending-decisions.md` decision 10)

## 2. Transport and prompted router

- [x] 2.1 Add a `ModelTransport` protocol and an `HttpTransport` (OpenAI-compatible JSON, timeout and bounded retry) raising a typed `ModelUnavailable`; verify with a unit test over a stub transport (evidence: `sentinel-ai-core/app/ai/transport.py`, tests; ref: `docs/build/areas/ml.md`)
- [x] 2.2 Add a `FixtureTransport` reading committed responses keyed by `prompt_version` and a normalized-input hash; verify a replay test returns the recorded result and a transport that raises on HTTP proves no connection is opened (evidence: `sentinel-ai-core/app/ai/fixtures/`, tests; ref: `docs/build/areas/ml.md`)
- [x] 2.4 Record the initial fixtures from one online run, review them for personal data, and verify the suite passes with the network transport disabled (evidence: `sentinel-ai-core/app/ai/fixtures/`, tests; refs: REQ-0028, REQ-0019)
- [x] 2.3 Implement `PromptedLLMRouter` (understand plus describe) with the configuration route table, the cheap pre-check and the default fallback; verify tests cover charge, missing, out-of-scope and person intents and pt-BR detection (evidence: `sentinel-ai-core/app/ai/llm.py`, `tests/test_ai_router.py`; refs: decision 007, decision 010, `docs/build/areas/ml.md`)

## 3. Identity and observability

- [x] 3.1 Pass `ModelInfo` and the result tokens and cost into the observer so the `understand` record carries the real model, route, prompt version, tokens and cost; verify a test asserts non-mock values and numeric cost on a router-served turn (evidence: `sentinel-ai-core/app/orchestrator/step.py`, `tests/test_observability.py`; refs: REQ-0019, REQ-0055, `openspec/specs/observability/spec.md`)

## 4. Gold alignment and PII guard

- [x] 4.1 Align the prompt and extraction schema to `ServiceDisputeEligibleTransaction` field names and numeric types, and add a request whitelist that rejects forbidden keys; verify a test asserts numeric amount and no `customer_id`, session token or PII column in the request (evidence: `sentinel-ai-core/app/ai/llm.py`, tests; refs: REQ-0047, `docs/understand/reference/latam-bank-data-dictionary.md`)
- [x] 4.2 Add a guard test that greps the request payload for the PII column names and confirm it stays consistent with the adversarial free-text path `A9` (evidence: `sentinel-ai-core/tests/test_ai_router.py`, `evidence/adversarial/20260930T214744Z/summary.json`; refs: REQ-0047, decision 004)

## 5. Failure handling

- [x] 5.1 On `ModelUnavailable`, retry a bounded number of times and then reply with a safe fallback and a handoff offer, never reporting success; verify a test injects a failing transport and asserts the fallback and handoff (evidence: `sentinel-ai-core/app/orchestrator/step.py`, tests; refs: REQ-0021, REQ-0026)

## 6. Integration

- [x] 6.1 Run the full `sentinel-ai-core` suite with the keyword baseline as default and confirm it is green, and confirm a replayed turn opens no connection (evidence: pytest output; ref: `sentinel-ai-core/README.md`)
- [x] 6.2 Update the requirements status for REQ-0001, REQ-0012, REQ-0019, REQ-0047 and REQ-0055 and note the router in `docs/build/areas/ml.md` (evidence: `docs/requirements/requirements.md`, `docs/build/areas/ml.md`)
