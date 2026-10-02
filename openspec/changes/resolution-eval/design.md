# Design

## Context

`run_case` in `eval/runner.py` posts the opening message and, when a case has `selected_reference`, one more request, then stops. `system_metrics` counts a turn as resolved only when its outcome is `case_confirmation`, which needs a third request. The sealed set has one turn per case and no selected reference, and `eval-v7`'s system block therefore reports 0 resolved of 75. The frozen run `eval-v7` also fails `python3 -m eval.run verify` on its system block, for a reason not yet found. The mock Gold store (`app/tools/gold.py`) holds 17 rows for three customers; only four are eligible, approved and below the thresholds (MX `TXN-1001`, `TXN-1006`; CO `TXN-2001`; AR `TXN-3001`). Router recordings live in `app/ai/fixtures/`, which ships inside the app image. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- A case can end as `case_confirmation`, and the rate is measured for baseline and router on the same cases.
- The statistics honestly reflect that the set has few distinct situations.

**Non-Goals:**
- Extending the mock store with new charges; the set uses what exists and says so.
- Fixing the unexplained `verify` mismatch of `eval-v7`; this change must not inherit it (see risks).

## Decisions

**1. A `confirm` flag on the case, one more request in the runner.** A case that sets `confirm` sends the selection, and if the reply is `confirm_box`, a second selection of the same charge, which the API treats as the confirmation. A refusal or handoff after the selection ends the case. Alternative: always confirm when a box appears; rejected because it would also confirm cases that must stop, and the harness should never decide that for the case.

**2. Situations are the unit of resampling.** A situation is a charge plus the rule it exercises (for example `TXN-2001`, eligible). Each is written in four variants. Intervals resample situations, the way `eval-v7` resamples bases. With about 4 eligible situations the resolution rate has a wide interval, and the report labels it descriptive when wider than ±10 points, as in [018](../../../docs/build/decisions/018-evaluation-acceptance.md).

**3. Size: 12 to 16 situations, 4 variants each, 48 to 64 cases.** Eligible: 4 situations. Must not resolve: outside the window (`TXN-1002`), refunded (`TXN-1003`), already disputed (`TXN-1004`), high amount per country (MX `TXN-1101`, CO `TXN-2002`, AR `TXN-3002`), fraud score per country (`TXN-1102`, `TXN-2003`, `TXN-3003`), "not mine". More messages per situation add little; more situations would need new store rows, which is out of scope.

**4. Baseline and router_v2 in one run, paired.** Same cases, session, store and reference date. The pairing reuses the paired net-difference code of `eval/paired.py`. The primary comparison is resolution and unsafe outcomes, not intent accuracy.

**5. Recordings in a separate directory.** Router answers for this run are recorded under `eval/` and not in `app/ai/fixtures/`, so the image does not carry evaluation-only recordings. The recorder takes a directory already. Spend cap as in `eval/budget.py`.

**6. Rules before the run, in a decision file.** An amendment to 018 or a new decision states the limits in cases, committed before any recording. Proposed content: 0 unsafe outcomes; 0 missed transfers among cases labelled must-hand-off; the router "beats" the baseline on resolution only if the interval of the paired net difference is above zero; a failure is reported as it is. The owner fixes the numbers; the sizes above bound what can be claimed.

**7. Not sealed, and said so.** The set is written by the team with the stores and rules already visible. Sealing by hash would imply isolation that does not hold. It is committed and fixed before the run, labelled as a simulation set, and never called held-out.

**8. New run id and kind.** A new run folder (for example `2024Q4-resolution-v1`) with its own `kind`, frozen through `freeze_run`, never touching `eval-v7` or `measured.json`.

## Risks / Trade-offs

- **Few situations.** Wide intervals, and the rate depends on four eligible charges. Mitigation: label descriptive, report counts, claim only that the path works and that policy refuses what it should.
- **The harness could confirm too eagerly.** Mitigation: the flag is on the case, and a scenario tests that refused charges send no third turn.
- **Inherited replay mismatch.** If the cause of the `eval-v7` system-block mismatch is a loop change since freezing, a new run replayed later after more loop changes will mismatch too. Mitigation: find that cause first (task 1.1), and freeze this run only after `dispute-answers` is merged, or record the commit it measured.
- **Authorship.** Cases written by the same team and model family as the system share its blind spots. Declared as in [018](../../../docs/build/decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing).
- **Simulation over a mock store.** A high resolution rate shows the logic works on test data, not that the service resolves real cases.
