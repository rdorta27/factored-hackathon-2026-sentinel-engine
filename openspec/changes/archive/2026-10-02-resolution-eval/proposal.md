# Proposal

## Why

The brief asks for "safe automated resolution" over all in-scope cases and for cost per successful resolution. Every measured run reports 0 of 75, and cost per resolution is "not defined" ([metrics report](../../../docs/build/metrics-report.md), REQ-0055). The cause is structural: a dispute needs three turns (message, select the charge, confirm), but the system runner sends at most two (`eval/runner.py`) and the sealed set has one turn per case. No case can end as `case_confirmation`, so the 0 measures the harness and not the system.

## What Changes

- The system runner sends the confirmation turn when a case asks for it, so a case can end with a verified case number.
- A new **resolution set** of multi-turn cases over the mock Gold store: eligible charges (should resolve), and charges that must be refused or handed off (outside the window, pending, refunded, already disputed, high amount, fraud score, "not mine"). Each case names its charge, country, language and expected outcome.
- One measurement of **baseline and router_v2 on the same cases**, paired, with intervals clustered by situation. Router answers are recorded once under a spend cap and replayed offline.
- Acceptance rules are written and committed **before** the run, as in [018](../../../docs/build/decisions/018-evaluation-acceptance.md).
- The result is frozen write-once and reported with safe automated resolution over in-scope cases, the share where automation was attempted, unsafe outcomes with denominators, and cost per attempted case and per resolution.
- Metrics report, README limitations and requirement evidence cite the new run.

## Capabilities

### New Capabilities
- `resolution-evaluation`: the multi-turn resolution set, its provenance, the paired baseline and router comparison, and the acceptance rules.

### Modified Capabilities
- `evaluation-runner`: the system runner can complete a confirmation turn and report resolution from it.

## Impact

- Code in `sentinel-ai-core/eval/` (runner, cases loader, freeze or run entry point, report); new cases under `eval/cases/`; recorded router answers under the existing fixtures.
- New frozen run under `evidence/evaluation-runs/`; `docs/build/metrics-report.md`, [018](../../../docs/build/decisions/018-evaluation-acceptance.md) amendment or a new decision, README, requirements REQ-0055 and REQ-0057.
- Not changed: the sealed set and its `measured.json` entry, `eval-v7`, the app, the policy files.

## Non-goals

- A new sealed held-out set. This set is committed and fixed before the run but not sealed; it is not presented as held-out intent accuracy.
- Real Gold data, production traffic or any claim of field resolution rate. The result is a simulation on a mock store.
- Router v3, greetings and `eval-v8`; they follow.
- ROI figures (REQ-0057 stays a labelled projection).

## Assumptions

- Baseline and router_v2 run on the same cases, as chosen by the owner.
- The mock store has few eligible charges, so the number of distinct situations, not the number of messages, limits the statistics; intervals cluster by situation and the report says so.
