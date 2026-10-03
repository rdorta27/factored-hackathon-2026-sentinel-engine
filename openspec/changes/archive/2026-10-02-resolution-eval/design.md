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

## Situations available in the mock store (task 1.2)

Read from `app/tools/gold.py` and `config/policy/{mx,co,ar}.yaml` (window 90 days, cutoff 2026-06-17). Every charge is the customer's own (`CUST-0001`/`CUST-0002`/`CUST-0003`); `TXN-9001` belongs to another customer and is not usable. Each situation is written in four cases: two in the account language (`es-MX`, `es-CO` or `es-AR`) and two in `pt-BR`, sharing the charge and the rule.

| Situation (`base_id`) | Country | Charge | Amount | Rule exercised | Expected outcome | Handoff |
|---|---|---|---|---|---|---|
| `eligible-mx-1001` | MX | `TXN-1001` | 1000.00 MXN | `status.approved` (allow) | `case_confirmation` | no |
| `eligible-mx-1006` | MX | `TXN-1006` | 320.00 MXN | `status.approved` (allow) | `case_confirmation` | no |
| `eligible-co-2001` | CO | `TXN-2001` | 250000.00 COP | `status.approved` (allow) | `case_confirmation` | no |
| `eligible-ar-3001` | AR | `TXN-3001` | 45000.00 ARS | `status.approved` (allow) | `case_confirmation` | no |
| `window-mx-1002` | MX | `TXN-1002` | 2500.00 MXN | `window.expired` (153 days) | `text` | no |
| `reversed-mx-1003` | MX | `TXN-1003` | 500.00 MXN | `status.reversed` (Refunded) | `text` | no |
| `disputed-mx-1004` | MX | `TXN-1004` | 750.00 MXN | `already.disputed` | `text` | no |
| `amount-mx-1101` | MX | `TXN-1101` | 8200.00 USD | `amount.high` (> 7584.74) | `handoff` | yes |
| `fraud-mx-1102` | MX | `TXN-1102` | 310.00 USD | `fraud.score` (29.6 > 28.51) | `handoff` | yes |
| `amount-co-2002` | CO | `TXN-2002` | 32000000.00 COP | `amount.high` (> 30332703.85) | `handoff` | yes |
| `fraud-co-2003` | CO | `TXN-2003` | 180000.00 COP | `fraud.score` (29.4 > 28.55) | `handoff` | yes |
| `amount-ar-3002` | AR | `TXN-3002` | 2900000.00 ARS | `amount.high` (> 2661378.62) | `handoff` | yes |
| `fraud-ar-3003` | AR | `TXN-3003` | 38000.00 ARS | `fraud.score` (29.3 > 28.49) | `handoff` | yes |
| `notmine-mx-1001` | MX | `TXN-1001` | 1000.00 MXN | `fraud.claim` (the customer says it is not theirs) | `handoff` | yes |

**Pending is not representable.** The spec lists a pending charge among the must-not-resolve situations, but no `Pending` row exists in the mock store, and this change does not add one (the app is out of scope). The set covers the status the store allows (`Refunded` → `status.reversed`) and says so in the report. The same table lives with the cases so the mapping stays checkable.

## Risks / Trade-offs

- **Few situations.** Wide intervals, and the rate depends on four eligible charges. Mitigation: label descriptive, report counts, claim only that the path works and that policy refuses what it should.
- **The harness could confirm too eagerly.** Mitigation: the flag is on the case, and a scenario tests that refused charges send no third turn.
- **Inherited replay mismatch.** If the cause of the `eval-v7` system-block mismatch is a loop change since freezing, a new run replayed later after more loop changes will mismatch too. Mitigation: find that cause first (task 1.1), and freeze this run only after `dispute-answers` is merged, or record the commit it measured.
- **Authorship.** Cases written by the same team and model family as the system share its blind spots. Declared as in [018](../../../docs/build/decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing).
- **Simulation over a mock store.** A high resolution rate shows the logic works on test data, not that the service resolves real cases.
