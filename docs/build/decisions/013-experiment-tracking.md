---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 013 · Experiment tracking in the frozen runs

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 14.

## Context

The kickoff asks for experiment tracking: model and prompt versions, parameters and metrics (REQ-0019). The options were MLflow (built into Databricks, decision 12), Azure ML, or another tool.

Each frozen evaluation run already writes the model, the route, the prompt version, the tokens, the cost, the latency and the label provenance. It writes them per turn and in its `summary.json`. The runs are write-once, and a command verifies them.

## Options

1. **MLflow now:** a known name. It needs a server or Databricks, and it copies what the runs already record. The time before the Friday freeze goes to setup, not to evidence.
2. **Azure ML:** the same cost, and a subscription that does not exist yet.
3. **The frozen runs as the tracking record.** Each run is a folder under `evidence/evaluation-runs/` with its versions, parameters and metrics. Nothing is overwritten.

## Decision

Option 3. The evaluation runs are the experiment log: one folder per run, never edited. Each run names its model, route, prompt version, labels and metrics. When decision 10 adds a live model, the same run records its parameters (model id per route, temperature, prompt version).

## Consequences

- No new tool to install, run or explain. Every number on the slides points to a run folder.
- To compare runs, compare their `summary.json` files. There is no dashboard.
- The [evidence index](../../../evidence/README.md#evaluation-runs) lists every run with its status (current or superseded) and its offline `verify` result.
- Production path: MLflow on Databricks, which the production pipeline already uses (decision 12). It reads the same fields.
- *Updated 10/5:* a training run is also a frozen run. `evidence/evaluation-runs/2024Q4-train-v1/` records the split ids, the regularization parameter, the validation scores, the pinned scikit-learn version and the hash of the model file. `python3 -m eval.run verify` trains again on the frozen split ids and compares the hash. The hash is valid only with the pinned scikit-learn version.
