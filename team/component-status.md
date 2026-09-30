# Component status

Where the build stands on Wed 9/30 evening: the same components as the [System Architecture](../docs/architecture/system-architecture.md), painted by status. Evidence per item lives in [tasks](tasks.md) and the [requirements](../docs/requirements/requirements.md).

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
        learned["Learned component<br/>fake port, no classifier yet"]
    end

    orch --> policy
    orch --> learned
    orch --> lookup & open & verify
    lookup --> goldmock[("Gold mock store<br/>no real read yet")]
    open --> disputes[("Dispute record<br/>in-memory")]
    verify --> disputes
    orch --> handoff(["Advisor handoff<br/>mock, no queue UI"])
    orch -.-> logs[("Structured logs<br/>traces, latency, cost")]
    evalr["Evaluation runner"] -.-> chat
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
    class chat,session,orch,policy,config,lookup,open,verify,disputes,logs,tests done
    class learned,goldmock,handoff,pipeline partial
    class evalr,deploy,s3 missing
    class client ext
```

## Reading it

- **Done (11):** the full demo path works — chat, session, loop, policy with per-country files, the three tools against fakes, the in-memory dispute record with read-back verification, the structured log with its JSONL file, and the measured [adversarial set](../evidence/adversarial/20260930T214744Z/summary.json) (29 attacks, `0/29` unsafe).
- **Partial (4):** the learned component is a fake port (the classifier comparison is the biggest open ML item); Gold is a mock store (the pipeline code exists with tests but never ran end to end); the advisor handoff is a stub with no queue UI.
- **Missing (3):** the evaluation runner (next, reads the new logs), the S3-to-service real read path, and the public deployment.

## What unblocks what

The evaluation runner is unblocked: it only needs the JSONL file this branch added. The classifier needs the held-out design first. Deployment needs whoever provides the subscription (see [To find out](tasks.md#to-find-out)).
