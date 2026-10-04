# Proposal

## Why

The evidence that the product works still has three holes once `resolution-eval` lands. Its run `2024Q4-resolution-v1` (16 of 56 resolved, 0 unsafe, for baseline and router_v2) measured the loop before `chat-loop`, so it must be measured again on the final loop. REQ-0024 and REQ-0050 rest on dataset reports, while the brief asks for the system's own outcomes by language and segment and for country monitoring of the app; Natalia agreed on 2026-10-02 to set both to In progress and that we derive them from the app's logs. And the kickoff names cost efficiency as a key metric, but there is no cost per resolution against the baseline or ROI, and the data has no advisor-hour cost (REQ-0055, REQ-0057, REQ-0024, REQ-0050, REQ-0017).

## What Changes

- **Breakdown in every new system run:** the mandatory outcome metrics per language variant and per account country, with n and a descriptive label for small groups.
- **Country monitoring from the turn log:** a script aggregates, per country and language, turns, p50 and p95 latency, failed or timed-out steps, escalations and handoffs, fallbacks and cost, aggregates only, from a replayed workload labelled simulated.
- **Final resolution run** (`2024Q4-resolution-v2`) on the same resolution set after `chat-loop`, under the rules already committed, with the breakdown.
- **ROI as a break-even:** a script reads call-center aggregates (handle time, first-contact resolution, escalation for the Transaccional reason) from Bronze, or from Silver if Natalia's columns have landed; a document gives the safe-resolution rate at which the system pays for itself, with a sensitivity table over an assumed advisor-hour range, every input labelled by origin.
- **Final metrics report** and requirement updates: REQ-0055 and REQ-0017 closed, REQ-0024 and REQ-0050 to In progress until this evidence, then Done.

## Capabilities

### New Capabilities
- `system-breakdown`: per-group outcomes in system runs, monitoring from the turn log, the segment limit.
- `roi-projection`: labelled inputs, aggregates without rows, the break-even rule.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/eval/` (grouping, monitor script, report), a script under `scripts/`, new folders under `evidence/`, `docs/build/roi.md`, `docs/build/metrics-report.md`, `docs/build/metrics.md`, `docs/build/areas/analysis.md`, requirement cards, README results.
- Not changed: frozen runs, the app, the pipeline.

## Non-goals

- Segment breakdown of system outcomes (cases carry no customer record; stated).
- A measured saving or a chosen advisor-hour price.
- Silver changes (Natalia's); the ROI script switches source only if they exist.

## Assumptions

- `resolution-eval` is merged first; this branch is rebased on it.
- Supersedes the changes `system-breakdown` and `roi-projection`.
