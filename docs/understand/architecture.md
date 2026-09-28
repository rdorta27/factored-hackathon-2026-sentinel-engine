# Architecture

How Sentinel Engine is put together for the transaction-disputes flow ([decision 003](../build/decisions/003-disputes-flow.md)). It runs on Azure; the parts of the stack that are still open are listed under [stack](#stack).

**Purpose:** see how the pieces fit before reading the areas. **Related:** [conversation](../build/conversation.md), [security](../build/security.md), [areas](../build/areas/), [glossary](glossary/), [architecture and roadmap](../build/architecture-roadmap.md).

## Central principle

**AI understands; code executes and verifies.** The LLM interprets the customer and drafts replies. Permissions, confirmations, actions and their verification live in code. This document is the source of that principle and of the layers below; [conversation](../build/conversation.md) turns it into rules for what the assistant says, and other documents link here rather than repeat it.

## Two layers

```mermaid
flowchart LR
    subgraph service["Service layer · real time"]
        direction TB
        client(["Customer"]) <--> frontend["Frontend<br/>chat"]
        frontend --> orch["Orchestrator · code + LLM<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]
        orch --> tools["Tools bound to the session<br/>look up transactions · open dispute<br/>look up dispute · handoff"]
        tools --> advisor(["Advisor<br/>simulated"])
        tools -- "write · read back" --> disputes[("Disputes store<br/>SQLite locally · Postgres on Azure")]
    end
    subgraph dataL["Data layer · batch or incremental"]
        direction TB
        files[("Dataset files<br/>partitions, late arrivals,<br/>duplicates, schema changes")] --> pipe["Pipeline Bronze → Silver → Gold<br/>contracts, dedup, upsert, quality"]
        pipe --> gold[("Gold<br/>transactions per customer<br/>with cutoff date")]
        pipe --> anstore[("Analytical data<br/>analysis, training, baseline")]
    end
    tools -- "read" --> gold

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class client,advisor ext
    class frontend,orch,tools,pipe real
    class files,gold,anstore,disputes store
```

- **Service layer:** what matters is latency, verified actions, bounded retries and idempotency.
- **Data layer:** what matters is quality, freshness and reproducibility. Every read returns the data **and how current it is**.
- **Two stores, two jobs.** Tools read transactions from Gold, which the pipeline fills in batches. Disputes are written to a small operational store, so the assistant can open one and read it back at once to verify it.

## Components and mocks

We start with mocks that have fixed contracts and replace them one at a time without changing the contract (see the [plan](../../team/plan.md#mocks)). Dashed orange: mock to implement. Blue: real component. Green: store that is real from the start.

```mermaid
flowchart TB
    client(["Customer"]) --> chat["Web chat<br/>login and confirmation"] --> auth["Authenticated session<br/>customer_id"] --> orch["Orchestrator<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]

    subgraph brain["Reasoning and control"]
        pii["Personal data (PII)<br/>masking"] --> llm["Hybrid LLM<br/>with router"]
        policy["Policy in code<br/>permissions, confirmation"]
        ml["Learned component<br/>vs baseline"]
    end
    subgraph toolset["Tools"]
        read["Look up<br/>transactions"]
        open["Open dispute<br/>idempotent"]
        verify["Look up<br/>dispute"]
        handoff["Handoff JSON"]
    end
    subgraph stores["Stores"]
        gold[("Transactions<br/>with cutoff date")]
        disputes[("Disputes<br/>store")]
        advisors[("Advisor<br/>queue")]
        traces[("Traces and<br/>audit log")]
    end

    orch --> pii & policy & ml
    orch --> read & open & verify & handoff
    read --> gold
    open --> disputes
    verify --> disputes
    handoff --> advisors
    orch -.-> traces
    s3[("S3 dataset")] --> pipeline["Pipeline<br/>Bronze → Silver → Gold"] --> gold

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class client ext
    class chat,orch,pii,policy,llm,pipeline real
    class auth,ml,read,open,verify,handoff,gold,disputes,advisors mock
    class traces,s3 store
```

- **Session:** a trusted test session. Every tool filters by its `customer_id`, never by an identifier typed in the chat.
- **Learned component:** starts as a fixed rule; when the model arrives, the rule stays as its baseline.
- **Disputes store:** SQLite locally and Postgres on Azure, separate from Gold. Opening a dispute is idempotent from the first version, so a retry never creates a duplicate.

## Decision priority

When several parts could decide, the higher one wins:

```mermaid
flowchart TD
    req(["Decision request"]) --> policy{"Does a policy<br/>rule apply?"}
    policy -- "yes" --> apply["Apply the rule<br/>permissions, confirmations,<br/>fixed escalations"]
    policy -- "no" --> learned{"Does the learned<br/>component weigh in?"}
    learned -- "yes" --> predict["Predictor decides<br/>e.g. escalation score"]
    learned -- "no" --> llm["LLM drafts the reply<br/>and picks a tool"]
    predict --> llm
    apply --> done(["Outcome"])
    llm --> done

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class req,done ext
    class apply,predict,llm real
```

1. **Policy in code.** Permissions, confirmations and fixed rules. Example: if the customer asks for a person, we escalate.
2. **Learned component**, when it takes part (e.g. an escalation predictor). It decides whether to escalate where no rule applies.
3. **LLM.** Understands the customer, drafts the reply and picks which tool to call. It never picks which customer to read.

## LLM visibility

- It sees the customer's text and the tool **results**.
- It **never** sees identifiers, documents, income, credit score or IP. The orchestrator knows the customer from the session.
- Details in [security](../build/security.md) and [decision 004](../build/decisions/004-pii-lifecycle.md).

## Walkthrough of a case (example: duplicate-charge dispute)

```mermaid
sequenceDiagram
    autonumber
    actor C as Customer
    participant F as Frontend (chat)
    participant O as Orchestrator<br/>(code + LLM)
    participant T as Tools<br/>(session-bound)
    participant S as Stores
    participant A as Advisor (simulated)

    C->>F: "me cobraron dos veces"<br/>("I was charged twice")
    F->>O: message + session
    rect rgba(91, 79, 214, 0.08)
    Note over O: Understand: intent = charge dispute<br/>(PII masked before the LLM)
    O->>T: Decide: search repeated purchases<br/>(session customer)
    T->>S: read transactions (Gold)
    S-->>T: candidate charges + cutoff date
    T-->>O: candidates
    O->>F: show candidates in their currency
    F->>C: candidates
    C->>F: picks one and confirms
    F->>O: confirmation
    end
    rect rgba(199, 125, 18, 0.10)
    O->>T: Act: open dispute (idempotency key)
    T->>S: write dispute (disputes store)
    O->>T: Verify: look up dispute
    T->>S: read dispute
    S-->>T: dispute exists
    T-->>O: case number
    end
    O->>F: case number and next step
    F->>C: case number
    opt a rule or the predictor calls for it
        O->>T: Escalate: handoff
        T->>A: JSON handoff (verified facts,<br/>open questions)
    end
```

1. The customer writes "me cobraron dos veces" ("I was charged twice").
2. **Understand:** the intent is a charge dispute.
3. **Decide:** details are missing, so a tool searches the session customer's repeated purchases.
4. The assistant shows the candidates in their original currency, with the data cutoff date. The customer picks one.
5. **Act:** after the customer confirms, a tool opens the dispute with an idempotency key.
6. **Verify:** a second tool reads the dispute back. Only when it exists does the customer get the case number.
7. **Escalate** when a rule or the predictor calls for it: a JSON handoff with verified facts and open questions.

## Learned component

Chosen at the Tuesday 9/29 review, together with the flow; the candidates are in [decision 003](../build/decisions/003-disputes-flow.md). Whatever we pick is measured against a baseline. Details in [ML](../build/areas/ml.md).

## Path to production

REQ-0052. Cloud deployment is not mandatory (mentors, 9/28); what counts is a credible path to production. The prototype keeps a minimal deployment for the public link and documents the rest.

| Aspect | Prototype | Production |
|---|---|---|
| Data | Local DuckDB with Bronze/Silver/Gold | Databricks on Azure (Delta Lake, SQL Warehouse) |
| Disputes store | SQLite | Postgres on Azure |
| Serving | One container behind the public link | Azure Container Apps with autoscaling |
| LLM | Hybrid router, usage caps | Same router, per-route quotas and fallback |
| Monitoring | Traces and audit log in files | Centralized logs, alerts by country |
| Security | Test session, masked PII, secrets in `.env` | Identity provider, Key Vault, retention policy |
| Volume | Sized to the sample (see [analysis](../build/areas/analysis.md#sizing)) | Capacity plan from real traffic |

## Stack

| Piece | Status |
|---|---|
| Platform | **Azure** ([decision 001](../build/decisions/001-azure-platform.md)) |
| Specifications | **OpenSpec** ([decision 002](../build/decisions/002-openspec.md)) |
| LLM | **Hybrid, with a router** between models. Which model serves each route: Tue 9/29 (decision 10) |
| Disputes store | **SQLite locally, Postgres on Azure**, separate from Gold |
| Data storage | Tue 9/29 (decision 12): local DuckDB or Databricks, both with Bronze/Silver/Gold. Meanwhile the pipeline starts locally |
| Backend | **Python + FastAPI** (decided). Loop tool deferred: LangGraph or plain Python ([decision 005](../build/decisions/005-backend.md)) |
| Frontend | **One-page chat served by FastAPI.** No Streamlit or Gradio ([decision 006](../build/decisions/006-frontend.md)) |
| Deployment | Open (decision 13); proposal: Azure Container Apps or App Service |
| Repositories | Open (decision 21): one repository or one per domain (proposed on 9/28). The submission requires a single public repository |

**Target:** the system runs on Azure and, locally, on Linux. .NET is out because it is not part of the team's stack (Python, FastAPI).

> [!WARNING]
> Windows is not a target, but a teammate may develop on it. Known friction: the commit hook is a bash script (it needs Git Bash), and local PySpark/Delta Lake needs Java and usually `winutils`. Work that runs remotely (Databricks, Azure) avoids both.

Each choice is recorded in [decisions](../build/decisions/).
