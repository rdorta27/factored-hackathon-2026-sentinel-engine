# Tasks

## 1. Engine and files

- [x] 1.1 Add `PolicyRequest`, `PolicyHit`, and `evaluate` with the first-match order. Owner: Rubén. Decision: [005](../../../docs/build/decisions/005-backend.md). Evidence: `sentinel-ai-core/tests/test_policy_engine.py` covers insist-before-status, day 90, day 91, null threshold, amount equal to the injected threshold, and an unknown country.
- [x] 1.2 Add synthetic `config/policy/mx.yaml`, `co.yaml`, and `ar.yaml` (currency only differs; thresholds null and provisional). Owner: Rubén. Area: [AI](../../../docs/build/areas/ai.md). Evidence: a test loads MX and rejects a missing file without returning `allow`.

## 2. Loop wiring

- [x] 2.1 Keep `person_asks` on conversation state and stop the person short-circuit in `step`. Pass country, demo date, and the count into `evaluate`. Owner: Rubén. Decision: [003](../../../docs/build/decisions/003-disputes-flow.md). Evidence: `sentinel-ai-core/tests/test_person_asks.py` for offer, then handoff, with zero `classify` calls.
- [x] 2.2 Re-evaluate before `open_dispute` on the confirmation turn. Reject the write unless the hit is `allow`. Call `classify` only after `allow`. Owner: Rubén. Area: [AI](../../../docs/build/areas/ai.md). Evidence: `sentinel-ai-core/tests/test_policy_gate.py` for a reversed charge and for a window that expires before confirm.
