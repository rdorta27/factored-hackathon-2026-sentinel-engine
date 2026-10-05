---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Capacity and latency

**Choice:** one replica serves the demo. The capacity limit is the CPU and memory limit of the replica, not the event loop.

**Why:** the brief asks for capacity limits ([REQ-0053](../requirements/analytics.md#req-0053)). The machine-learning engineer of Factored warned that CPU-bound work can block the FastAPI event loop. The load run measures the service on one process with recorded answers, so it measures the code and not the provider.

**Evidence:** [`robustness/20261005T211031Z`](../../evidence/robustness/20261005T211031Z/summary.json), script `scripts/load_chat.py`.

| Mode | Target rps | `achieved_rps` | `p95_ms` | `errors` | `rejected_429` |
|---|---|---|---|---|---|
| Host, recorded | 5 | 4.82 | 35.7 | 0 | 0 |
| Host, recorded | 10 | 9.59 | 46.3 | 0 | 0 |
| Host, recorded | 20 | 17.51 | 79.0 | 0 | 0 |
| Container 0.5 vCPU, 1 GiB | 5 | 4.29 | 99.7 | 0 | 0 |
| Container 0.5 vCPU, 1 GiB | 10 | 5.62 | 202.6 | 0 | 0 |
| Container 0.5 vCPU, 1 GiB | 20 | 4.54 | 918.2 | 0 | 0 |

The container reaches its limit between the targets 10 and 20: the achieved rate falls and the p95 rises to `recorded_container` 918 ms. The host has no limit, so the same code reaches `recorded_local` 17.51 rps. The event loop does not block: the error count and the 429 count stay at zero.

The live part of the run shows the model latency: `live_local` reaches 0.66 rps at the target 2, with p50 1394 ms and p95 3870 ms. The frozen live run [`2024Q4-resolution-live-v1`](../../evidence/evaluation-runs/2024Q4-resolution-live-v1/summary.json) reports `timing.per_call.p50` 2087.89 ms and `timing.per_call.p95` 5217.76 ms per call.

**Alternatives rejected:** autoscaling. SQLite is per instance, so a second replica would split the state. A load test on the public link. It costs the evaluators and one replica serves the demo.

**In production:** many replicas behind a load balancer, a shared database and a queue for the slow model calls. The limit moves from one CPU to the provider.

**On the slide:** "One replica serves about ten requests a second at the deployed limits. The model, not the loop, sets the latency."

Traces to [REQ-0053](../requirements/analytics.md#req-0053).
