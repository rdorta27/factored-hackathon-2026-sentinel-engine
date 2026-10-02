# Component status

Where the build stands on Thu 10/1: the same components as the [System Architecture](../docs/architecture/system-architecture.md), painted by status. Evidence per item lives in [tasks](tasks.md) and the [requirements](../docs/requirements/requirements.md).

Legend: green = implemented and tested · amber = partial (works behind a mock, offline only, or not run on real data) · red = missing.

```mermaid
flowchart TB
    client(["Customer"]) --> chat["Chat page · POST /api/v1/chat<br/>confirm box"]
    client --> dapi["Disputes API<br/>preview → create · list"]
    chat --> session["Session and conversation state<br/>SQLite, retention on logout/expiry"]
    dapi --> session
    session --> orch["Orchestrator<br/>U → D → A → V → E"]

    subgraph control["Control · code"]
        policy["Policy engine"]
        config[("Policy configuration<br/>per country and currency · synthetic")]
        policy --> config
    end
    subgraph toolset["Session-bound tools"]
        lookup["lookup_transactions"]
        open["open_dispute"]
        verify["lookup_dispute"]
        handoff["handoff"]
    end
    subgraph brain["Understanding"]
        learned["Keyword baseline served ·<br/>prompted router offline (mirrored)"]
    end

    orch --> policy
    orch --> learned
    orch --> lookup & open & verify & handoff
    lookup --> gold[("Gold<br/>mock · DuckDB adapter")]
    open --> cases[("Case store · SQLite<br/>disputes · tickets")]
    verify --> cases
    handoff --> cases
    cases --> aview["Advisor view<br/>GET /api/v1/handoffs"]
    orch -.-> logs[("Structured logs<br/>traces, latency, cost")]
    evalr["Evaluation runner<br/>44 cases, 0 failures"] -.-> chat
    evalr -.-> logs
    tests["Adversarial set<br/>36 attacks, 0/36 unsafe<br/>free text masked"] -.-> chat
    tests -.-> dapi
    tests -.-> aview
    s3[("S3 raw data")] --> pipeline["Bronze → Silver → Gold<br/>end-to-end run, quality report partial"]
    pipeline --> gold
    deploy["Public deployment"] -.-> chat

    classDef done fill:#d9f5e3,stroke:#1f9d55,stroke-width:2px,color:#12351f
    classDef partial fill:#fff3d6,stroke:#b7791f,stroke-width:2px,color:#4a3200
    classDef missing fill:#ffe3e3,stroke:#d33f3f,stroke-width:2px,color:#4a1111
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class chat,dapi,session,orch,policy,config,lookup,open,verify,handoff,cases,aview,logs,evalr,tests done
    class learned,gold,pipeline partial
    class deploy missing
    class s3 done
    class client ext
```

## Reading it

- **Done (16):** policy configuration with synthetic fraud and high-amount thresholds per account country and currency ([010](../docs/build/decisions/010-fraud-handoff-rule.md), [011](../docs/build/decisions/011-high-amount-threshold.md)); the full demo path on one app and one API under `/api/v1`: chat and the two-step disputes API on the same turn cycle, password session with roles, conversation state in SQLite that survives a restart and is deleted on logout or expiry, the loop and policy engine, the four tools with one open dispute per charge and read-back verification, handoff tickets with a conversation summary and every attempted action, the read-only advisor view, the structured log, free-text personal-data masking before the model, the [latest evaluation run](../evidence/evaluation-runs/2024Q4-eval-v6/summary.json) (44 cases, 0 failures) and the [latest adversarial run](../evidence/adversarial/20261001T222341Z/summary.json) (36 attacks, `0/36` unsafe, A9 blocked); the S3 raw data synced locally.
- **Partial (3):** understanding (the demo serves the keyword baseline; the prompted router is measured offline against mirrored fixtures, so the delta is zero by construction until decision 10); Gold (the pipeline writes the view into `data/gold_bank.duckdb`, but the adapter reads a Delta table under `data/gold/`, so the app still falls back to the mock); the pipeline (run end to end with incremental tests, sources inventoried and sizing written, but the quality report lacks nulls, orphans and late arrivals).
- **Missing (1):** the public deployment.

## What unblocks what

The measured pieces are frozen: router, label evidence and runner are archived with their specs (`llm-router`, `evaluation-evidence`, `evaluation-runner`); the integration, persistence and advisor work merged with PR #23 on 10/1; its three OpenSpec changes and `add-fraud-and-high-amount-rules` are archived under `openspec/changes/archive/` (2026-10-01), with the main specs synced. What remains open: the live model per route and serving it (decision 10, re-record fixtures and freeze a new run id), the Gold real read in the app (DuckDB file versus Delta view), how the system serves Portuguese without Portuguese data (decision 15, REQ-0012), the deployment subscription (see [To find out](tasks.md#to-find-out)), and the presentation and video on the frozen build.
