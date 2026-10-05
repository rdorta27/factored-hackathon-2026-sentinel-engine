---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Rehearsal v8 (offline, development only)

- Cases: 198 development. No sealed case read. No live call.
- Spend: USD 0.0 over 0 live calls (cap 0.45). Time 4.9 s.

## Component (offline fixtures)

- baseline: kind 0.5909 (n=198); subtype 0.0 (0/40); slots not defined (0/0); rejected 0/0; unsafe wording 0/0.
- router_v1: kind 0.1515 (n=198); subtype 0.0 (0/40); slots not defined (0/0); rejected 0/0; unsafe wording 0/0.
- router_v2: kind 0.0 (n=198); subtype 0.0 (0/40); slots not defined (0/0); rejected 0/0; unsafe wording 0/0.

## System sample (baseline fixture replay, 40 cases)

- Unnecessary handoffs: 0/40.
- Outcome match: 40/40.
- Ceiling: 0 of 21 resolvable of 40 (gap 21).
- Latency per conversation p50/p95 ms: 0.94/1.38.

## Limits

- Offline fixtures only: trained baseline, live v3 and cut-off variants are missing.
- Fixture scores check the pipeline only. They do not rank the models.
- The full rehearsal runs every candidate with the spend cap before the freeze.
