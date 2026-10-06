---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [025](../../../docs/build/decisions/025-charge-selector.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

**Mode.** Ask the owner for the three inputs of the proposal first. Task 2.2 needs them. Every other task is automatic. Never push, open a pull request or create a tag. Do not change the files that decide behavior (see the design). This change runs at the same time as `live-ops`.

**Priority (the submission is due on 2026-10-05, 11:59 PM COT).** Required: 1.1 to 1.4 and 2.1 to 2.4. Next: 2.5 and 3.1. Cut first: 2.6 and 3.2.

## 1. Build the measurement

- [x] 1.1 Write `eval/measure_v8.py` with the commands `measure RUN_ID [--record] [--cap USD]`, `verify RUN_ID` and `verdict RUN_ID`. `measure` verifies the seals of `eval/cases/sealed_v8` and `eval/cases/sealed_v8b`, refuses a hash that `eval/measured.json` lists, runs the six candidates (`baseline`, `trained_baseline`, `router_v2`, `router_v2_cutoffs`, `router_v3`, `router_v3_cutoffs`) on the intent, noisy, attack and multi-turn blocks and on the top-up block, computes the v8 metrics of `eval/rehearse_full.py`, the paired differences of D4 to D7, three repeats of the high-risk subset, cost and latency, and freezes one run with `freeze_run`. It records the two hashes only after the freeze. Evidence: the script.
- [x] 1.2 Test the script with a fake transport and a fake sealed set: it refuses a second measurement, refuses a modified seal, stops at the cap without freezing and leaves `eval/measured.json` unchanged on a failure. Evidence: the tests.
- [x] 1.3 Run the script in a dry-run mode on development data only (no sealed case read, `eval/measured.json` unchanged). Cap USD 0.45. Compare its numbers with `2024Q4-rehearsal-v8`. Evidence: the comparison in `eval/review/measure-v8-dry-run.md`.
- [x] 1.4 Write `verdict` as a script: for each candidate it prints the result of zero unsafe wording, D4, D5, D6, D7, kind accuracy of at least 0.93 and subtype accuracy of at least 0.95, and the served choice (v3 without cut-offs only if it passes every gate, otherwise v2). Evidence: the script and a test on a fake summary.

## 2. Measure and decide (after the owner inputs)

- [x] 2.1 Check the preconditions: a clean working tree, no entry of the v8 or v8b hash in `eval/measured.json`, both seals verify, `.env` has the model key, and the commit and the `bundle_hash` are recorded in the commit body. Evidence: the output.
- [x] 2.2 Measure once: `python3 -m eval.measure_v8 measure 2024Q4-eval-v8 --record --cap <input>`. Freeze `evidence/evaluation-runs/2024Q4-eval-v8/` and add it to `evidence/README.md` (Simulation, live model calls, mock store). If the run stops before the freeze, fix the cause and run it again: the recordings are kept and the sets are not yet measured. Never run it again after the freeze. Evidence: `summary.json`, `report.md` and `eval/measured.json`.
- [x] 2.3 Verify the run offline with `python3 -m eval.measure_v8 verify 2024Q4-eval-v8`. The run reports DIFFERS in `router_v3` and `router_v3_cutoffs` only: 30 transient `unavailable` calls that a later pass recorded. The owner accepts the frozen run and the difference is documented in 018. Evidence: the verify output and 018.
- [x] 2.4 Run `verdict`. Write the result in decision 018 (a dated section "Result v8"): the table of gates, the served choice and the failed rule if any. Set the answer for `post-freeze`: the value of `SENTINEL_LLM_PROMPT_VERSION` for the redeploy. Evidence: decision 018 and the verdict output.
- [x] 2.5 Update `docs/build/metrics-report.md`, the results table of the README, `evidence/README.md` and the evidence of REQ-0016, REQ-0022 and REQ-0055. Cite fields of `summary.json`. Do not copy a number by hand. Say that a failed gate is a result, not an error. Evidence: those files.
- [x] 2.6 Write `docs/rationale/router-error-analysis.md`: the ten most frequent confusions with case ids, cause and kind of fix; accuracy by intent with the number of bases; a note on the intents with fewer than 10 bases. Cite fields only. Label the cases as team-written simulation. Evidence: the page.

## 3. Requirements and team

- [x] 3.1 Update the cards of REQ-0016, REQ-0022 and REQ-0055 with the new evidence. Change a status only where the evidence exists. Evidence: `docs/requirements/`.
- [x] 3.2 Update `team/tasks.md` and `team/plan.md`. Evidence: the two files.
