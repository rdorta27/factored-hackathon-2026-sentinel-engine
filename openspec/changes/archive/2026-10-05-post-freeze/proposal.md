# Proposal

## Why

Four plans hold tasks that cannot run before the code freeze: `eval-v8` (the single measurement and the verdict), `robustness-evidence` (fault and load runs, the rationale pages), `live-ops` (the final redeploy) and `pitch-site` (the final numbers). These tasks keep four branches open although their code is finished. They also run in a fixed order: the measurement, then the runs, then the redeploy, then the numbers. One plan owns that order and the freeze gate that starts it (REQ-0016, REQ-0021, REQ-0026, REQ-0035, REQ-0050, REQ-0053; decisions 018 and 025).

## What Changes

- **Freeze gate:** the owner confirms that all code is merged, the served configuration is chosen and the local end-to-end check passes. The freeze commit and the `bundle_hash` of `/health` are recorded.
- **Measure:** `2024Q4-eval-v8` is measured once, each candidate is judged by the 018 amendment, and the router errors are analyzed with concrete cases.
- **Runs:** the fault-injection run and the load run are frozen, and the four robustness rationale pages are written.
- **Redeploy:** one redeploy from `main`, checked remotely and queried by country, outcome and language.
- **Close:** the final numbers go to the site and the slides, the README and the changelog are reviewed, and the owner gets the tag commands.

The tasks move from the other plans. No task is new work except the error analysis and the gate.

## Capabilities

### New Capabilities
- `post-freeze-closure`: the gate, the single measurement, the verdict, the error analysis, the runs and the final redeploy.

### Modified Capabilities
(none)

## Impact

- `evidence/evaluation-runs/2024Q4-eval-v8/`, `evidence/robustness/`, `eval/measured.json`, `deploy/azure/`, `site/numbers.json`, `docs/rationale/`, REQ-0016, REQ-0021, REQ-0026, REQ-0035, REQ-0050, REQ-0053.
- Not changed: application code, the sealed sets, the amendment.

## Non-goals

- New features, new sealed cases or a second measurement of a sealed hash.
- Code changes after the gate. A needed fix reopens the gate and repeats the affected runs.
- Producing the video (plan `video`).

## Assumptions

- `eval-v8`, `robustness-evidence`, `live-ops` (tasks 1.1 to 1.3), `pitch-site` and `charge-ranker` are merged before the gate.
- The owner runs the tag commands.
