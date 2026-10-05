---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Failure handling

**Choice:** a model failure or a tool failure ends in a safe reply or a handoff. The keyword baseline answers a failed model call.

**Why:** the brief asks for bounded retries, safe fallback and tool-failure handling with counts ([REQ-0021](../requirements/non-functional.md#req-0021), [REQ-0026](../requirements/non-functional.md#req-0026)). A failed model call must not stop the turn and must not invent a fact.

**Evidence:** [`robustness/20261005T210525Z`](../../evidence/robustness/20261005T210525Z/summary.json). The run drives the local app through seven faults with 12 turns each. It uses the keyword baseline and the Gold mock. The faults come from the ports (`app/tools/faults.py`), so no code path exists only for the test.

| Fault | Field | Value |
|---|---|---|
| None, the healthy baseline | `faults.none.safe_share` | 1.0 (12 of 12) |
| Model timeout | `faults.model-timeout.safe_share` | 1.0 (12 of 12) |
| Model 5xx | `faults.model-5xx.safe_share` | 1.0 (12 of 12) |
| Invalid model JSON | `faults.model-json.safe_share` | 1.0 (12 of 12) |
| Slow Gold | `faults.gold-slow.safe_share` | 1.0 (12 of 12) |
| Gold error | `faults.gold-error.safe_share` | 1.0 (12 of 12) |
| Case-store error | `faults.store-error.safe_share` | 0.833 (10 of 12) |

The baseline answers every model fault. The slow Gold adds about 6 s per turn (`faults.gold-slow.latency_ms.p50`) and still answers every turn. The store error leaves 2 of 12 turns unsafe: one client read error and one unparseable reply.

The suite also proves three safeguards: two parallel confirmations open one case (`tests/test_confirmation.py`), a pending confirmation expires after five minutes, and each audit record holds the hash of the one before (`tests/test_audit_chain.py`).

**Alternatives rejected:** retry without a limit. A failing model would hold the turn open. A general try/except around the turn. It hides the failure and breaks the safe-reply count.

**In production:** the store error is the weak point. Production uses PostgreSQL with a connection pool and a retry. The model fallback stays.

**On the slide:** "When the model or a tool fails, the rules still answer. The run counts every failure, and the store error is the one gap we name."

Traces to [REQ-0021](../requirements/non-functional.md#req-0021) and [REQ-0026](../requirements/non-functional.md#req-0026).
