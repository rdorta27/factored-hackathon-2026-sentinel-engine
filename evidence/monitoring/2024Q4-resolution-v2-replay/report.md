# Country monitoring /tmp/opencode/eval-final-var/turns.jsonl

Workload: 256 turns in 888 records, 2026-10-03T14:17:11.673148+00:00 to 2026-10-03T14:17:23.913261+00:00 (simulated).

| Country | Language | Turns | Latency p50/p95 ms | Failed/timed-out steps | Escalations | Handoffs | Fallback turns | Cost USD |
|---|---|---|---|---|---|---|---|---|
| AR | es-419 | 28 | 0.79/1.29 | 0 | 8 | 8 | 0 | 0.001916 |
| AR | pt-BR | 28 | 0.91/1.41 | 0 | 8 | 8 | 0 | 0.0 |
| CO | es-419 | 28 | 0.79/1.28 | 0 | 8 | 8 | 0 | 0.001916 |
| CO | pt-BR | 28 | 0.84/1.41 | 0 | 8 | 8 | 0 | 0.0 |
| MX | es-419 | 72 | 0.78/1.31 | 0 | 12 | 12 | 0 | 0.00514 |
| MX | pt-BR | 72 | 0.82/1.43 | 0 | 12 | 12 | 0 | 0.0 |

## Notes
- Aggregates only: no trace id, session reference or text.
- A country outside MX, CO and AR is reported apart under other.
- Understand records carry the session language before detection, so model cost lands under the pre-detection language group.
- Replayed workload, labelled simulated: not field behaviour.
