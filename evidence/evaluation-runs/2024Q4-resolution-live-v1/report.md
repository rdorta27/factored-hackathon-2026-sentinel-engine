# Resolution measurement 2024Q4-resolution-live-v1

Eval 2026-09-30+runner-v1 · simulation over a mock store · n=56 cases in 14 situations · commit a3db6bb687e2.

> Simulation over a mock store, not a field resolution rate (decision 022).
> Timing: live. The latency and the cost come from live model calls under the spend cap. The numbers are end-to-end.

## Safe resolution by version

| Version | Safe resolutions | Share | Containment | Missed | Unnecessary | Unsafe outcomes | Cost per attempted | Cost per resolution |
|---|---|---|---|---|---|---|---|---|
| baseline | 16 of 56 | 0.2857 | 0.5 | 0 | 0 | 0 (0/56) | 0.0 | 0.0 |
| router_v2 | 16 of 56 | 0.2857 | 0.5 | 0 | 0 | 0 (0/56) | 0.00016 | 0.000561 |

## Timing (router_v2)

- Mode: live.
- Per model call p50/p95 ms: 2087.89/5217.76 (n=56)
- Per conversation p50/p95 ms: 2187.95/5310.84 (n=56)
- Cost per attempted case / per resolution USD: 0.00016 / 0.000561
- The latency and the cost come from live model calls under the spend cap. The numbers are end-to-end.

## Paired resolution (router_v2 vs baseline)

- fixed 0, broken 0, net 0 of 56 (0.0), interval [0.0, 0.0], above zero: False

## Breakdown by language variant (safe resolution, situations as clusters)

| Group | Version | Resolved | Share | 95% interval |
|---|---|---|---|---|
| es-AR | baseline | 2 of 6 | 0.3333 | [0.0, 1.0] (descriptive) |
| es-AR | router_v2 | 2 of 6 | 0.3333 | [0.0, 1.0] (descriptive) |
| es-CO | baseline | 2 of 6 | 0.3333 | [0.0, 1.0] (descriptive) |
| es-CO | router_v2 | 2 of 6 | 0.3333 | [0.0, 1.0] (descriptive) |
| es-MX | baseline | 4 of 16 | 0.25 | [0.0, 0.625] (descriptive) |
| es-MX | router_v2 | 4 of 16 | 0.25 | [0.0, 0.625] (descriptive) |
| pt-BR | baseline | 8 of 28 | 0.2857 | [0.0714, 0.5714] (descriptive) |
| pt-BR | router_v2 | 8 of 28 | 0.2857 | [0.0714, 0.5714] (descriptive) |

## Breakdown by account country (safe resolution, situations as clusters)

| Group | Version | Resolved | Share | 95% interval |
|---|---|---|---|---|
| AR | baseline | 4 of 12 | 0.3333 | [0.0, 1.0] (descriptive) |
| AR | router_v2 | 4 of 12 | 0.3333 | [0.0, 1.0] (descriptive) |
| CO | baseline | 4 of 12 | 0.3333 | [0.0, 1.0] (descriptive) |
| CO | router_v2 | 4 of 12 | 0.3333 | [0.0, 1.0] (descriptive) |
| MX | baseline | 8 of 32 | 0.25 | [0.0, 0.625] (descriptive) |
| MX | router_v2 | 8 of 32 | 0.25 | [0.0, 0.625] (descriptive) |

Groups with an interval wider than ±10 points are descriptive; per-country groups of this size are descriptive by construction.
System outcomes are not broken down by customer segment: cases carry no customer record, so there is nothing to group by.

## Acceptance rules (decision 022)

- R1 safe: PASS — baseline 0/56; router_v2 0/56
- R2 no missed transfers: PASS — baseline 0; router_v2 0
- R3 router resolves more (interval above zero): not above zero
- R4 router unsafe outcomes: PASS

Spend: USD 0.008977 over 56 live calls (cap 1.0). Prices: Fireworks model library, 2026-10-01 (decision 016).

## Notes
- Team-written simulation cases, never dataset rows (decision 007).
- Simulation over a mock store: not a field resolution rate (decision 022).
- Baseline and router_v2 on the same cases, session, store and reference date; intervals resample situations.
- The system block replays the loop at measured_commit; a later loop change means a new run (task 1.1).
