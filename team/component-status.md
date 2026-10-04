# Component status

Where the build stands on Fri 10/2, after PR #50: the same components as the [System Architecture](../docs/architecture/system-architecture.md), painted by status. Evidence per item lives in [tasks](tasks.md) and the [requirements](../docs/requirements/requirements.md).

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
        learned["router_v2 served ·<br/>baseline fallback"]
    end

    orch --> policy
    orch --> learned
    orch --> lookup & open & verify & handoff
    lookup --> gold[("Gold<br/>DuckDB file locally · mock on the link")]
    open --> cases[("Case store · SQLite<br/>disputes · tickets")]
    verify --> cases
    handoff --> cases
    cases --> aview["Advisor view<br/>GET /api/v1/handoffs"]
    orch -.-> logs[("Structured logs<br/>traces, latency, cost")]
    evalr["Evaluation runner<br/>eval-v7 · resolution-v1"] -.-> chat
    evalr -.-> logs
    tests["Adversarial set<br/>42 attacks, 0/42 unsafe<br/>none without defence"] -.-> chat
    tests -.-> dapi
    tests -.-> aview
    s3[("S3 raw data")] --> pipeline["Bronze → Silver → Gold<br/>end-to-end run, report not generated in full"]
    pipeline --> gold
    deploy["Public deployment<br/>router_v2 live, image before PRs #49–#50"] -.-> chat

    classDef done fill:#d9f5e3,stroke:#1f9d55,stroke-width:2px,color:#12351f
    classDef partial fill:#fff3d6,stroke:#b7791f,stroke-width:2px,color:#4a3200
    classDef missing fill:#ffe3e3,stroke:#d33f3f,stroke-width:2px,color:#4a1111
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class chat,dapi,session,orch,policy,config,lookup,open,verify,handoff,cases,aview,logs,evalr,tests,learned,gold done
    class pipeline,deploy partial
    class s3 done
    class client ext
```

## Reading it

- **Done (18):** the full demo path on one app and one API under `/api/v1`: chat and the two-step disputes API, password session with roles, conversation state in SQLite deleted on logout or expiry, the loop and the policy engine with synthetic fraud and high-amount thresholds per account country and currency ([010](../docs/build/decisions/010-fraud-handoff-rule.md), [011](../docs/build/decisions/011-high-amount-threshold.md)), the four tools with read-back verification, handoff tickets and the read-only advisor view, the structured log, free-text masking; understanding (router_v2 served with a baseline fallback, measured in `2024Q4-eval-v7`; narrowing by what the customer said, the "why?" answer, the prompt-extraction refusal and the injection record in code, PRs #42 and #49); Gold (the app reads the PII-free view from the DuckDB file locally, PR #50); the evaluation (`2024Q4-eval-v7`, `2024Q4-resolution-v1`) and the [latest adversarial run](../evidence/adversarial/20261002T222323Z/summary.json) (42 attacks, `0/42` unsafe, none left without defence).
- **Partial (2):** the pipeline (end to end with incremental tests and Silver columns restored in PR #44, but the quality report's drop, orphan, late-arrival and null sections are written by hand and the next run overwrites them: `quality-report`); the public deployment (router_v2 is live, but the image predates PRs #49 and #50 and state is on the ephemeral disk: redeploy and `runtime-and-ci`).
- **Missing (0).** Small talk is still classified out of scope (`router-v3`); system outcomes per language and country and app monitoring are `evaluation-final`.

## What unblocks what

Merged and archived: `dispute-answers`, `resolution-eval`, `chat-loop`, `real-gold`. Open changes, each on its own branch: `runtime-and-ci` (in progress), `quality-report` (Natalia), `ui-product`, `evaluation-final` (unblocked by `chat-loop`), then `router-v3`.
