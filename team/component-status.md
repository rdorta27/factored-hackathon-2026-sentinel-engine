# Component status

Where the build stands on Wed 9/30 night: the same components as the [System Architecture](../docs/architecture/system-architecture.md), painted by status. Evidence per item lives in [tasks](tasks.md) and the [requirements](../docs/requirements/requirements.md).

Legend: green = implemented and tested · amber = partial (works behind a mock or fake) · red = missing.

```mermaid
flowchart TB
    client(["Customer"]) --> chat["Chat page · POST /chat<br/>confirm box"]
    chat --> session["Session<br/>and conversation state"]
    session --> orch["Orchestrator<br/>U → D → A → V → E"]

    subgraph control["Control · code"]
        policy["Policy engine"]
        config[("Policy configuration<br/>per country")]
        policy --> config
    end
    subgraph toolset["Session-bound tools · in-memory fakes"]
        lookup["lookup_transactions"]
        open["open_dispute"]
        verify["lookup_dispute"]
    end
    subgraph brain["Understanding · LLM"]
        learned["Prompted router<br/>measured vs baseline (mirrored)"]
    end

    orch --> policy
    orch --> learned
    orch --> lookup & open & verify
    lookup --> goldmock[("Gold mock store<br/>no real read yet")]
    open --> disputes[("Dispute record<br/>in-memory")]
    verify --> disputes
    orch --> handoff(["Advisor handoff<br/>mock, no queue UI"])
    orch -.-> logs[("Structured logs<br/>traces, latency, cost")]
    evalr["Evaluation runner<br/>35 cases, 0 failures"] -.-> chat
    evalr -.-> logs
    tests["Adversarial set<br/>29 attacks, 0/29 unsafe"] -.-> chat
    tests -.-> session
    s3[("S3 raw data")] --> pipeline["Bronze → Silver → Gold<br/>code with tests, no end-to-end run"]
    pipeline --> goldmock
    deploy["Public deployment"] -.-> chat

    classDef done fill:#d9f5e3,stroke:#1f9d55,stroke-width:2px,color:#12351f
    classDef partial fill:#fff3d6,stroke:#b7791f,stroke-width:2px,color:#4a3200
    classDef missing fill:#ffe3e3,stroke:#d33f3f,stroke-width:2px,color:#4a1111
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class chat,session,orch,policy,config,lookup,open,verify,disputes,logs,tests,learned,evalr done
    class goldmock,handoff,pipeline partial
    class deploy,s3 missing
    class client ext
```

## Reading it

- **Done (14):** the full demo path works — chat, session, loop, policy with per-country files, the three tools against fakes, the in-memory dispute record with read-back verification, the structured log with its JSONL file, the measured [adversarial set](../evidence/adversarial/20260930T214744Z/summary.json) (29 attacks, `0/29` unsafe), the prompted router with fixtures and safe fallback, and the [frozen evaluation run](../evidence/evaluation-runs/2024Q4-eval-v1/summary.json) (35 cases, 0 failures, unsafe `0/35`).
- **Partial (3):** Gold is a mock store (the pipeline code exists with tests but never ran end to end); the advisor handoff is a stub with no queue UI; the router-vs-baseline delta is zero by construction (mirrored fixtures — the live-model comparison needs decision 010).
- **Missing (2):** the S3-to-service real read path and the public deployment.

## What unblocks what

The measured pieces are frozen: router, label evidence and runner are archived with their specs (`llm-router`, `evaluation-evidence`, `evaluation-runner`). What remains open: the live model per route (decision 10, re-record fixtures and freeze a new run id), the Gold real read, the deployment subscription (see [To find out](tasks.md#to-find-out)), and the presentation and video on the frozen build.
