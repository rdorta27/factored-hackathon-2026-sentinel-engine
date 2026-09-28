# Architecture

How Sentinel Engine is put together for the transaction-disputes flow ([decision 003](../build/decisions/003-disputes-flow.md)). It runs on Azure; the parts of the stack that are still open are listed under [stack](#stack).

**Purpose:** see how the pieces fit before reading the areas. **Related:** [conversation](../build/conversation.md), [security](../build/security.md), [areas](../build/areas/), [glossary](glossary/), [architecture and roadmap](../build/architecture-roadmap.md).

## Central principle

**AI understands; code executes and verifies.** The LLM interprets the customer and drafts replies. Permissions, confirmations, actions and their verification live in code. This document is the source of that principle and of the layers below; [conversation](../build/conversation.md) turns it into rules for what the assistant says, and other documents link here rather than repeat it.

## Two layers

```mermaid
flowchart LR
    subgraph service["SERVICE LAYER (real time)"]
        client["Customer"] <--> frontend["Frontend (chat)"]
        frontend --> orch["Orchestrator (code + LLM)<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]
        orch --> tools["Tools (bound to the session)<br/>· look up transactions<br/>· open dispute · look up dispute<br/>· handoff"]
        tools --> handoff["Handoff JSON → agent (simulated)"]
        tools -- "write / read back" --> disputes[("Disputes store<br/>SQLite locally, Postgres on Azure")]
    end
    subgraph dataL["DATA LAYER (batch or incremental)"]
        files["Dataset files<br/>(date partitions, late<br/>arrivals, duplicates, changing<br/>schema)"]
        files --> pipe["Pipeline Bronze → Silver → Gold:<br/>contracts, deduplication,<br/>upsert, quality"]
        pipe --> gold[("Gold<br/>transactions per customer,<br/>with cutoff date")]
        pipe --> anstore["Analytical data<br/>(analysis, training, baseline)"]
    end
    tools -- "read" --> gold
```

- **Service layer:** what matters is latency, verified actions, bounded retries and idempotency.
- **Data layer:** what matters is quality, freshness and reproducibility. Every read returns the data **and how current it is**.
- **Two stores, two jobs.** Tools read transactions from Gold, which the pipeline fills in batches. Disputes are written to a small operational store, so the assistant can open one and read it back at once to verify it.

## Components and mocks

We start with mocks that have fixed contracts and replace them one at a time without changing the contract (see the [plan](../../team/plan.md#mocks)). Dashed orange: mock to implement. Blue: real component.

```mermaid
flowchart TB
    client([Customer]) --> chat["Web chat<br/>login and confirmation"] --> auth["Authenticated session<br/>customer_id"] --> orch["Orchestrator<br/>Understand → Decide<br/>→ Act → Verify<br/>→ Escalate"]

    orch --> pii["Personal-data<br/>masking"] --> llm["Hybrid LLM<br/>with router"]
    orch --> policy["Policy in code<br/>permissions and confirmation"]
    orch --> ml["Learned component<br/>vs baseline"]
    orch --> read["Look up<br/>transactions"] --> gold[("Transactions<br/>with cutoff date")]
    orch --> open["Open dispute<br/>idempotent"] --> disputes[("Disputes<br/>store")]
    orch --> verify["Look up<br/>dispute"] --> disputes
    orch --> handoff["Handoff JSON"] --> agents[("Agent<br/>queue")]
    orch -.-> traces[("Traces and<br/>audit log")]
    s3[("S3: dataset")] --> pipeline["Pipeline<br/>Bronze → Silver → Gold"] --> gold

    classDef mock fill:#fff4e5,stroke:#e8a33d,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef real fill:#eef0ff,stroke:#6c5ce7,stroke-width:2px,color:#1b1640
    class auth,ml,read,open,verify,handoff,gold,disputes,agents mock
    class client,chat,orch,pii,policy,llm,pipeline,traces,s3 real
```

- **Session:** a trusted test session. Every tool filters by its `customer_id`, never by an identifier typed in the chat.
- **Learned component:** starts as a fixed rule; when the model arrives, the rule stays as its baseline.
- **Disputes store:** SQLite locally and Postgres on Azure, separate from Gold. Opening a dispute is idempotent from the first version, so a retry never creates a duplicate.

## Decision priority

When several parts could decide, the higher one wins:

```mermaid
flowchart TD
    req["Decision request"] --> policy{"Policy in code?"}
    policy -- "rule matches" --> apply["Apply rule<br/>(permissions, confirmations,<br/>fixed escalations)"]
    policy -- "no rule" --> learned{"Learned component<br/>weighs in?"}
    learned -- yes --> predict["Predictor decides<br/>(e.g. escalation score)"]
    learned -- no --> llm["LLM drafts and picks<br/>a tool to call"]
    predict --> llm
    apply --> done(["Outcome"])
    llm --> done
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
    participant C as Customer
    participant F as Frontend (chat)
    participant O as Orchestrator<br/>(code + LLM)
    participant T as Tools<br/>(with session)
    participant S as Stores
    participant A as Agent (simulated)
    C->>F: "me cobraron dos veces"<br/>("I was charged twice")
    F->>O: message + session
    Note over O: Understand: intent = charge dispute<br/>(personal data masked before the LLM)
    O->>T: Decide: search repeated purchases<br/>(session customer)
    T->>S: read transactions
    S-->>T: candidate charges + cutoff date
    T-->>O: candidates
    O->>F: show candidates in their currency
    F->>C: candidates
    C->>F: picks one and confirms
    F->>O: confirmation
    O->>T: Act: open dispute (idempotency key)
    T->>S: write dispute
    O->>T: Verify: look up dispute
    T->>S: read dispute
    S-->>T: dispute exists
    T-->>O: case number
    O->>F: case number and next step
    F->>C: case number
    opt a rule or the predictor says so
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

## Stack

| Piece | Status |
|---|---|
| Platform | **Azure** ([decision 001](../build/decisions/001-azure-platform.md)) |
| Specifications | **OpenSpec** ([decision 002](../build/decisions/002-openspec.md)) |
| LLM | **Hybrid, with a router** between models. Which model serves each route: Tue 9/29 (decision 10) |
| Disputes store | **SQLite locally, Postgres on Azure**, separate from Gold |
| Data storage | Tue 9/29 (decision 12): local DuckDB or Databricks, both with Bronze/Silver/Gold. Meanwhile the pipeline starts locally |
| Backend | Open (decision 9); proposal: Python with FastAPI |
| Frontend | Open (decision 11): Streamlit, Gradio or our own web app (Python or Node) |
| Deployment | Open (decision 13); proposal: Azure Container Apps or App Service |
| Repositories | Open (decision 21): one repository or one per domain (Natalia's proposal). The submission requires a single public repository |

**Target:** the system runs on Azure and, locally, on Linux. .NET is out because it is not part of the team's stack (Python, FastAPI).

> [!WARNING]
> Windows is not a target, but a teammate may develop on it. Known friction: the commit hook is a bash script (it needs Git Bash), and local PySpark/Delta Lake needs Java and usually `winutils`. Work that runs remotely (Databricks, Azure) avoids both.

Each choice is recorded in [decisions](../build/decisions/).
