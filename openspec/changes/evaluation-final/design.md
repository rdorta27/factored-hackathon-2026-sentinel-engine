# Design

## Context

After `resolution-eval`, the runner sends the confirmation turn, the resolution set holds 14 situations (56 cases) over the mock store, `system_metrics` computes the mandatory metrics from per-turn results that carry `locale` and `country`, and `eval.run verify` replays a resolution run offline. Records in `var/turns.jsonl` carry `language`, `country`, `step`, `outcome`, `latency_ms`, `model`, `route`, `cost_usd`, `policy_rule` and `handoff`. Read-only aggregates on 2026-10-02: Transaccional is 240,056 of 686,296 calls, mean handle time 3.68 minutes, first-contact resolution 0.915, escalation 0.099, 96,234 calls without duration; Queja is 7.2 minutes and 0.436. Silver drops `duration_seconds`; Bronze has it. Infrastructure is estimated at USD 20 to 60 a month (`docs/build/cost.md`). See proposal.md for motivation.

## Decisions

1. **Grouping inside the metrics module:** `system_metrics` per variant and per country, intervals with the run's resampling unit (situations), descriptive above ±10 points.
2. **Monitoring workload from the resolution replay:** the v2 run writes its records to a temporary `SENTINEL_VAR_DIR`; the monitor script reads that log, so the workload is known and reproducible, labelled simulated. Logs in Azure (from `runtime-and-ci`) can be read by the same script but are not committed.
3. **Re-measure, do not edit:** `2024Q4-resolution-v2` uses the committed rules and the same set; `v1` stays as the pre-`chat-loop` reference and the report shows both.
4. **Break-even over savings:** with AI cost per case around a hundredth of a cent, fixed cost dominates; the break-even needs volume, handle time and an assumed hour range only. The document states the headroom finding plainly: humans resolve 91.5% of transactional calls at first contact in 3.7 minutes, so savings per call are small.
5. **Source switch for the ROI script:** read Silver when `duration_seconds` exists there, else Bronze, and record which.

## Risks / Trade-offs

- **Small groups:** per-country groups of 56 cases are descriptive; no disparity is claimed without an interval.
- **Proxy:** Transaccional is broader than disputes; Queja's 7.2 minutes is reported to bound it.
- **A low break-even looks like a win:** it is conditional on an assumed hour and a simulated rate; said next to the number.
