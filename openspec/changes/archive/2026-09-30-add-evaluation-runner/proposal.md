# Proposal

## Why

The brief requires at least one learned component compared against a baseline on
held-out data with n, case mix and variability (REQ-0016, REQ-0017, REQ-0020,
REQ-0022) and the mandatory outcome metrics (REQ-0055). The router and the frozen
label set exist after their own changes, but there is no harness: no case set, no
metrics, no replay. Nothing can be measured or reported.

## What Changes

- Add `sentinel-ai-core/eval/` with a versioned, team-written case set (JSONL)
  carrying component labels (expected intent and category) and system labels
  (expected outcome, handoff, locale, country), plus edge and adversarial tags.
- Add a component benchmark that runs the prompted router and the keyword
  baseline over the same intent cases and computes the four pillars: intent
  metrics (accuracy and per-class precision, recall and F1 by locale), safety
  pass rate on cases that must not pass, an automation proxy, and stability
  across repeated runs.
- Add a system runner that replays cases against `POST /chat` with a test session
  and fault injection, reads the structured logs by `trace_id`, and computes the
  mandatory outcome metrics (safe resolution, unsafe outcomes, escalation
  quality, p50/p95 latency, cost).
- Add a shared metrics module and a report writer producing `summary.json` and
  `report.md` with n, case mix, model and prompt versions, and variability,
  including the failures.
- Freeze each run write-once under `evidence/evaluation-runs/<run-id>/` and cite
  its `summary.json`.

## Non-goals

- Implementing the router or the baseline: separate change.
- The dataset evidence and the label derivation: separate change.
- Choosing the model per route: pending decision 10.
- An LLM judge (REQ-0023, P2): only if time allows.

## Capabilities

### New Capabilities

- `evaluation-runner`: replays labelled conversations and computes the component
  and system metrics the brief requires.

### Modified Capabilities

None.

## Impact

- New: `sentinel-ai-core/eval/` and `evidence/evaluation-runs/`.
- Depends on `add-prompted-llm-router` (one model port and offline fixtures) and
  `add-evaluation-evidence` (the pinned `labels.json`).
- Requirements: REQ-0016, REQ-0017, REQ-0019, REQ-0020, REQ-0021, REQ-0022,
  REQ-0024, REQ-0025, REQ-0055, REQ-0057; decision 007.
