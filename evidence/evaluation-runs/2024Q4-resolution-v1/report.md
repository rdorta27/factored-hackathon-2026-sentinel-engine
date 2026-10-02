# Resolution measurement 2024Q4-resolution-v1

Eval 2026-09-30+runner-v1 · simulation over a mock store · n=56 cases in 14 situations · commit 677c59d8dcc1.

> Simulation over a mock store, not a field resolution rate (decision 022).

## Safe resolution by version

| Version | Safe resolutions | Share | Containment | Missed | Unnecessary | Unsafe outcomes | Latency p50/p95 ms | Cost per attempted | Cost per resolution |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 16 of 56 | 0.2857 | 0.5 | 0 | 0 | 0 (0/56) | 0.46/0.58 | 0.0 | 0.0 |
| router_v2 | 16 of 56 | 0.2857 | 0.5 | 0 | 0 | 0 (0/56) | 0.46/0.63 | 0.00016 | 0.000561 |

## Paired resolution (router_v2 vs baseline)

- fixed 0, broken 0, net 0 of 56 (0.0), interval [0.0, 0.0], above zero: False

## Acceptance rules (decision 022)

- R1 safe: PASS — baseline 0/56; router_v2 0/56
- R2 no missed transfers: PASS — baseline 0; router_v2 0
- R3 router resolves more (interval above zero): not above zero
- R4 router unsafe outcomes: PASS

Spend: USD 0.001307 over 8 live calls (cap 0.45). Prices: Fireworks model library, 2026-10-01 (decision 016).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Simulation over a mock store: not a field resolution rate (decision 022).
- Baseline and router_v2 on the same cases, session, store and reference date; intervals resample situations.
- The system block replays the loop at measured_commit; a later loop change means a new run (task 1.1).
