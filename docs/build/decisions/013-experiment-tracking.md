# 013 · Experiment tracking in the frozen runs

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 14.

## Context

The kickoff asks for experiment tracking: model and prompt versions, parameters and metrics (REQ-0019). The options were MLflow (built into Databricks, decision 12), Azure ML, or another tool.

Every frozen evaluation run already writes, per turn and in its `summary.json`, the model, route, prompt version, tokens, cost, latency and the label provenance, and runs are write-once and verifiable.

## Options

1. **MLflow now:** a known name, but it needs a server or Databricks and duplicates what the runs already record. Time before Friday's freeze goes to setup, not to evidence.
2. **Azure ML:** same cost, plus a subscription that does not exist yet.
3. **The frozen runs as the tracking record.** Each run is a folder under `evidence/evaluation-runs/` with its versions, parameters and metrics; nothing is overwritten.

## Decision

Option 3. The evaluation runs are the experiment log: one folder per run, never edited, each naming its model, route, prompt version, labels and metrics. When decision 10 adds a live model, its parameters (model id per route, temperature, prompt version) are recorded in the same run.

## Consequences

- No new tool to install, run or explain; every number in the slides points to a run folder.
- Comparing runs means comparing their `summary.json` files, not a dashboard.
- Production path: MLflow on Databricks, which the production pipeline already uses (decision 12), reading the same fields.
