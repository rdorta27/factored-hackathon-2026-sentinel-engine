# Design

## Context

Four plans split their work in two: what can run now and what needs frozen code. `eval-v8` sealed its set on 2026-10-05 and waits to measure. `robustness-evidence` finished its code (11 of 11 tasks). `live-ops` has the stable salt, the replay list and `scripts/e2e_check.py` before the gate. This plan holds the second half of each.

## Decisions

1. **One order:** measure, then runs, then redeploy, then numbers. A later step reads the frozen output of an earlier one. The measurement goes first because its verdict can change the served prompt (`SENTINEL_LLM_PROMPT_VERSION`).
2. **The gate records the code:** the freeze commit and `bundle_hash` are written down. After the redeploy, `/health` must show the same hash. This proves the measured behavior is the served behavior. The hash does not cover HTML, CSS or JavaScript, so the owner can still adjust the look of the page.
3. **A fix after the gate reopens the gate:** the affected runs repeat. The sealed measurement does not repeat (decision 018).
4. **Error analysis uses frozen output only:** it cites case ids and `summary.json` fields, and it labels the cases as team-written simulation.
5. **Tags stay with the owner:** the plan prepares the commands. It does not run `git push` or `git tag`.

## Risks / Trade-offs

- **A failed gate in `eval-v8`:** `router_v2` stays the default and the report states the failed rule. The plan still closes.
- **Log ingestion delay:** queries run a few minutes after the traffic.
- **Model spend:** the measurement and the small live run use the model. The spend caps of the amendment and of `robustness-evidence` apply.
