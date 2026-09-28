# Architecture

System overview for the transaction-disputes flow ([decision 003](../build/decisions/003-disputes-flow.md)). Platform: Azure; the open parts of the stack are listed under [stack](#stack).

**Purpose:** understand how the pieces fit together before reading the areas. **Related:** [conversation](../build/conversation.md), [security](../build/security.md), [areas](../build/areas/), [glossary](glossary/).

## Central principle

**AI understands; code executes and verifies.** This document is the source of this principle and of the layers; the conversation rules that follow from it live in [conversation](../build/conversation.md). Other documents link here instead of repeating it.

## Two layers

```mermaid
flowchart LR
    subgraph service["SERVICE LAYER (real time)"]
        client["Client"] <--> frontend["Frontend (chat)"]
        frontend --> orch["Orchestrator (code + LLM)<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]
        orch --> tools["Tools (with session)<br/>· look up transactions<br/>· open claim · look up claim<br/>· handoff"]
        tools --> handoff["Handoff JSON → agent (simulated)"]
    end
    subgraph dataL["DATA LAYER (batch or incremental)"]
        files["Dataset files<br/>(date partitions, late<br/>arrivals, duplicates, changing<br/>schema)"]
        files --> pipe["Pipeline: contracts,<br/>deduplication, upsert, quality"]
        pipe --> opstore["Operational store<br/>(mock of the banking<br/>core, per customer)"]
        pipe --> anstore["Analytical store<br/>(analysis, training, baseline)"]
    end
    tools -- "read / write" --> opstore
```

- **Service layer:** latency, action verification, retries, and idempotency matter.
- **Data layer:** quality, freshness, and reproducibility matter. Every read returns the data **and how current it is**.

## Components and mocks

We start with mocks that have fixed contracts and replace them one by one without changing the contract (see the [plan](../../team/plan.md#mocks)). Dashed orange: mock to implement. Blue: real component.

```mermaid
flowchart TB
    client([Customer]) --> chat["Web chat<br/>login and confirmation"] --> auth["Authenticated session<br/>customer_id"] --> orch["Orchestrator<br/>Understand → Decide<br/>→ Act → Verify<br/>→ Escalate"]

    orch --> pii["Personal-data<br/>masking"] --> llm["Hybrid LLM<br/>with router"]
    orch --> policy["Policy in code<br/>permissions and confirmation"]
    orch --> ml["Learned component<br/>vs baseline"]
    orch --> read["Look up<br/>transactions"] --> gold[("Transactions<br/>with cutoff date")]
    orch --> open["Open claim<br/>idempotent"] --> claims[("Claims<br/>system")]
    orch --> verify["Look up<br/>claim"] --> claims
    orch --> handoff["Handoff JSON"] --> agents[("Agent<br/>queue")]
    orch -.-> traces[("Traces and<br/>audit log")]
    s3[("S3: dataset")] --> pipeline["Pipeline<br/>Bronze → Silver → Gold"] --> gold

    classDef mock fill:#fff4e5,stroke:#e8a33d,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef real fill:#eef0ff,stroke:#6c5ce7,stroke-width:2px,color:#1b1640
    class auth,ml,read,open,verify,handoff,gold,claims,agents mock
    class client,chat,orch,pii,policy,llm,pipeline,traces,s3 real
```

- **Session:** a trusted test session; every tool filters by its `customer_id`, never by an identifier typed in the chat.
- **Learned component:** starts as a fixed rule, which stays as the baseline once the model arrives.
- **Claims system:** an operational store separate from Gold, so a claim can be written and read back at once to verify it.

## Decision priority

Highest to lowest:

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

1. **Policy in code.** Permissions, confirmations, and fixed rules (for example: if the customer asks to speak to a person, we escalate).
2. **Learned component**, if it takes part in the decision (e.g., an escalation predictor). It decides whether escalation is worthwhile where there is no rule.
3. **LLM.** Understands the customer, drafts responses, and chooses which tool to call; it never chooses which customer to read from.

## LLM visibility

- The customer text and tool **results**.
- **Never:** identifiers, documents, income, credit score, or IP. The orchestrator knows who the customer is from the session.
- Detail in [security](../build/security.md).

## Walkthrough of a case (example: duplicate-charge claim)

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
    Note over O: Understand: intent = charge claim<br/>(personal data masked before the LLM)
    O->>T: Decide: search repeated purchases<br/>(session customer)
    T->>S: read transactions
    S-->>T: candidate charges + cutoff date
    T-->>O: candidates
    O->>F: show candidates in their currency
    F->>C: candidates
    C->>F: picks one and confirms
    F->>O: confirmation
    O->>T: Act: open claim (idempotency key)
    T->>S: write claim
    O->>T: Verify: look up claim
    T->>S: read claim
    S-->>T: claim exists
    T-->>O: case number
    O->>F: case number and next step
    F->>C: case number
    opt a rule or the predictor says so
        O->>T: Escalate: handoff
        T->>A: JSON handoff (verified facts,<br/>open questions)
    end
```

1. The customer writes: "me cobraron dos veces" ("I was charged twice").
2. **Understand:** intent = charge claim.
3. **Decide:** data is missing, so the tool searches the session customer's repeated purchases.
4. The assistant shows the candidate charges in their currency and with the data cutoff date. The customer picks one.
5. **Act:** it asks for confirmation and the tool opens the claim with an idempotency key, so a retry does not duplicate it.
6. **Verify:** a second tool reads the claim back; only when it exists do we give the case number to the customer.
7. **Escalate** if the predictor or a rule indicates it: JSON handoff with verified facts and open questions.

## Learned component

We decide it together with the flow; with the transaction-disputes flow, the candidates are in [decision 003](../build/decisions/003-disputes-flow.md). Whichever it is, we compare it against a baseline. Detail in [ML](../build/areas/ml.md).

## Stack

| Piece | Choice |
|---|---|
| Platform | **Azure** ([decision 001](../build/decisions/001-azure-platform.md)) |
| Specifications | **OpenSpec** ([decision 002](../build/decisions/002-openspec.md)) |
| LLM | **Hybrid, with a router** between models; which model goes on each route is decided on Tue 29/9 |
| Data storage | To be decided on Tue 29/9: local DuckDB or Databricks, both with Bronze/Silver/Gold. Meanwhile the pipeline starts locally |
| Backend | To be decided; proposal: Python with FastAPI |
| Frontend | To be decided: Streamlit, Gradio or a custom web app (Python or Node) |
| Deployment | To be decided; proposal: Azure Container Apps or App Service |
| Repositories | To be decided: one repository or one per domain (Natalia's proposal); delivery requires a single public repository |

**Constraint:** everything must install and run the same way on Linux and Windows, so no platform-specific tooling (such as .NET).

We record each choice in [decisions](../build/decisions/).
