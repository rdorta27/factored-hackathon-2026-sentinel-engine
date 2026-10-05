---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

`eval-v8` sealed two held-out sets and rehearsed every candidate on development data. The single measurement and the verdict were left for later. Two things are missing:

- **No tool measures the sealed v8 sets.** `python3 -m eval.run measure` reads only the v7 seal, and the v7 hash is already measured. `eval/rehearse_full.py` reads development data only. The command that measures `sealed_v8` and `sealed_v8b` does not exist.
- **The verdict decides what the public link serves.** If v3 passes every gate of decision 018, the link serves it. The redeploy and the video wait for that verdict.

This change builds the measurement command, runs it once, and applies the gates. It cites REQ-0016, REQ-0017, REQ-0020, REQ-0022 and REQ-0055 and decisions 018 and 025.

## Owner inputs

The session asks for three inputs before it runs a sealed case:

- The confirmation that the served code is frozen from now on (see the design).
- The total spend allowed for live model calls.
- The OK for the single measurement of each sealed set.

## What Changes

- **A measurement command** for the two sealed sets. It checks both seals, refuses a set that is already measured, runs six candidates with a spend cap, repeats the high-risk subset three times, freezes one run, and then records both hashes as measured.
- **A verdict command** that applies the gates of decision 018 and prints one table. It does not use judgment.
- **One measurement**, then the reports: the metrics report, the README results, the evidence index, the requirement cards and decision 018.

## Capabilities

### New Capabilities
- `v8-measurement`: the single measurement of the sealed v8 sets and its verdict.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/eval/`, `evidence/evaluation-runs/2024Q4-eval-v8/`, `docs/build/`, `README.md`, `docs/requirements/`, decision 018.

## Non-goals

- A change to the prompt, the policy, the cut-offs, the templates or the router code after the freeze (decision 025).
- A second measurement of a sealed set.
- The redeploy and the checks on the link (`post-freeze`).
