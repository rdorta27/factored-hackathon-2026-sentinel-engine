# Tasks

## 1. Types and package

- [x] 1.1 Add `sentinel-ai-core` with the candidate charge, conversation state, turn input, and turn output shapes from design.md. Owner: Rubén. Area: [AI](../../../docs/build/areas/ai.md). Evidence: `sentinel-ai-core/app/orchestrator/` imports in a unit test that rejects a candidate missing currency.
- [x] 1.2 Add the policy function for closed rules (Pending, Reversed, Declined, person request) and treat a missing fraud or amount threshold as no rule. Owner: Rubén. Decision: [005](../../../docs/build/decisions/005-backend.md). Evidence: `sentinel-ai-core/tests/test_policy.py` covers status block, person handoff, and missing threshold.

## 2. Tool port and confirmation turn

- [x] 2.1 Add session-bound tool ports and in-memory fakes. `open_dispute` rejects a missing token and returns the existing record for a repeated idempotency key. Owner: Rubén. Area: [AI](../../../docs/build/areas/ai.md). Evidence: `sentinel-ai-core/tests/test_tools.py`.
- [x] 2.2 Implement `step` for text and for a structured candidate id: confirm box with no token, then token plus up to three read-back attempts on the same key. Owner: Rubén. Decision: [005](../../../docs/build/decisions/005-backend.md). Evidence: `sentinel-ai-core/tests/test_confirmation.py` for written yes, unknown id, success, and three failed lookups.

## 3. Demo cases

- [x] 3.1 Add the fake model port (`understand`, `classify`) and tests for the normal, ambiguous or unsupported, and human cases in `es-419` and `pt-BR`. Assert outcome kind, not wording. A duplicate charge is the normal case with another category. Owner: Rubén. Decision: [007](../../../docs/build/decisions/007-learned-component.md). Evidence: `sentinel-ai-core/tests/test_demo_cases.py`.
