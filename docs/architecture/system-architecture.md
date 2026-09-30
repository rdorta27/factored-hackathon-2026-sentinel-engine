# System Architecture

Target architecture of Sentinel Engine for the transaction-disputes flow: an account inquiry about a charge that becomes a dispute only when it has to. The [Demo Architecture](demo-architecture.md) has the same sections and diagrams, with the mocked parts marked. Behaviour and contracts are in the [Architecture Specification](specification.md).

Legend for every diagram: violet = component, blue = data store, grey = outside the system.

## Central principle

**AI understands; code executes and verifies.** The LLM interprets the customer and drafts replies. Permissions, confirmations, actions and their verification live in code. The loop is the one the hackathon asks for: **Understand → Decide → Act → Verify → Escalate**.

## Layers

```mermaid
flowchart LR
    subgraph dataL["Data layer · batch · sentinel-data-engine"]
        direction TB
        s3[("S3 raw data<br/>13 tables · MX · CO · AR")] --> bronze["Bronze<br/>append-only, audit columns"]
        bronze --> silver["Silver<br/>schema and quality rules,<br/>deduplicated"]
        silver --> quarantine[("Quarantine<br/>rejected_records")]
        silver --> gold[("Gold<br/>dispute serving tables")]
    end
    subgraph service["Service layer · one FastAPI process · sentinel-ai-core"]
        direction TB
        client(["Customer"]) <--> chat["One-page chat"]
        chat --> orch["Orchestrator<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]
        orch --> tools["Session-bound tools"]
        tools -- "write · read back" --> disputes[("Dispute record")]
        tools -- "JSON handoff" --> advisor(["Advisor"])
    end
    tools -- "read minimal view" --> gold

    classDef comp fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef store fill:#fbfaff,stroke:#3d8bff,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class bronze,silver,chat,orch,tools comp
    class s3,quarantine,gold,disputes store
    class client,advisor ext
```

- **Data layer.** Batch medallion pipeline. Bronze keeps the files as received; Silver enforces the schema contracts and quality rules and sends invalid rows to quarantine instead of dropping them; Gold holds denormalised tables ready to serve. The service reads Gold and never writes to it.
- **Service layer.** One process serves the chat page and `POST /chat`; there is no second app and no advisor screen.
- **Two stores, two jobs.** Charges are read from Gold, which the pipeline refreshes in batches. Disputes are written to an operational dispute record and read back at once, so the customer only hears a case number that exists.

## Components

```mermaid
flowchart TB
    client(["Customer"]) --> chat["Chat page · POST /chat<br/>confirm box"]
    chat --> session["Session<br/>and conversation state"]
    session --> orch["Orchestrator<br/>U → D → A → V → E"]

    subgraph understand["Understanding · LLM"]
        router["LLM router"]
        learned["Learned component<br/>dispute-category classifier"]
    end
    subgraph control["Control · code"]
        policy["Policy engine"]
        config[("Policy configuration<br/>per country")]
        policy --> config
    end
    subgraph toolset["Session-bound tools"]
        lookup["lookup_transactions"]
        open["open_dispute"]
        verify["lookup_dispute"]
        handoff["handoff"]
    end

    orch --> router & learned & policy
    orch --> lookup & open & verify & handoff
    lookup --> gold[("Gold<br/>minimal view")]
    open --> disputes[("Dispute record")]
    verify --> disputes
    handoff --> advisor(["Advisor"])
    orch -.-> logs[("Structured logs<br/>traces, latency, cost")]
    evalr["Evaluation runner"] -.-> chat
    evalr -.-> logs

    classDef comp fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef store fill:#fbfaff,stroke:#3d8bff,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class chat,session,orch,router,learned,policy,lookup,open,verify,handoff,evalr comp
    class config,gold,disputes,logs store
    class client,advisor ext
```

| Component | Role |
|---|---|
| Chat page and `POST /chat` | The customer's only entry point. State-changing actions are confirmed with a confirm box, not with free text. |
| Session and conversation state | Trusted session that carries `customer_id`; recent turns and pending confirmation, deleted when the session expires. |
| Orchestrator | Runs the loop and owns every call. It injects `customer_id` into tools; the LLM never sees or chooses it. |
| LLM router | Sends each LLM call to a model by route. Understands intent, language and the charge; drafts the reply. |
| Learned component | See [below](#learned-component). |
| Policy engine and configuration | Evaluates rules in code (status, eligibility, confirmation, handoff triggers) with per-country parameters from configuration. A policy outcome is final. |
| Tools | Four functions bound to the session: look up charges, open a dispute (idempotent), read it back, hand off. |
| Dispute record | Operational store for disputes. Relational; the engine is not decided (SQLite and PostgreSQL are candidates). Never Gold. |
| Structured logs | One record per loop step, used for tracing, monitoring and evaluation metrics. |
| Evaluation runner | Replays labelled conversations against `POST /chat` and computes the metrics the brief asks for. |

## Walkthrough of a case

```mermaid
sequenceDiagram
    actor C as Customer
    participant O as Orchestrator
    participant L as LLM
    participant P as Policy
    participant T as Tools
    participant G as Gold
    participant D as Dispute record
    participant A as Advisor

    C->>O: "I don't recognize this charge"
    O->>L: message, no identifiers
    L-->>O: intent, language, charge hints
    alt ambiguous or out of scope
        O->>C: clarifying question or abstain
    else charge inquiry
        O->>T: lookup_transactions
        T->>G: read (session customer)
        G-->>T: candidates, status, as-of date
        T-->>O: candidates
        O->>P: evaluate
        alt Pending, Reversed or Declined
            O->>C: explain the status, no dispute
        else fraud, high amount or asks for a person
            O->>T: handoff
            T-->>A: JSON package
            O->>C: an advisor takes over
        else dispute applies
            O->>L: learned component: dispute category
            O->>C: confirm box (candidate)
            C->>O: confirm
            O->>T: open_dispute (token, idempotency key)
            T->>D: write
            O->>T: lookup_dispute
            T->>D: read back
            D-->>O: record exists
            O->>C: case number
        end
    end
```

A timeout is not success: if the read-back fails after bounded retries, the case is handed off and no case number is given.

## Learned component

The one learned component is a **dispute-category classifier**: a prompted LLM with few-shot examples that reads the customer's message and assigns the dispute category, using the category and subcategory values of the `complaints` table (for example, the subcategory *Cargo no reconocido*, "unrecognized charge").

```mermaid
flowchart LR
    msg(["Customer message<br/>es-419 · pt-BR"]) --> cls["Prompted LLM<br/>few-shot classifier"]
    cls --> cat["Dispute category"]
    cat --> open["open_dispute<br/>category field"]
    base["Keyword baseline"] -. "same held-out cases" .- cls

    classDef comp fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class cls,cat,open,base comp
    class msg ext
```

- **Where it runs:** in Decide, only after policy has established that a dispute applies.
- **What it decides:** the category recorded in the dispute. It never decides eligibility and never overrides a rule.
- **How it is judged:** against a keyword baseline and the same LLM zero-shot, on the same held-out conversations. Because the dataset has no usable customer text, those conversations are team-written in `es-419` and `pt-BR` and declared as such.

## Stack and deployment

| Piece | Target |
|---|---|
| Platform | Azure; Linux for local development |
| Backend | Python and FastAPI, one process; loop implementation (LangGraph or plain Python) deferred |
| Frontend | One-page chat served by the same process, styled with the `branding/` files |
| Data pipeline | Delta Lake: DuckDB locally, Azure Databricks in production, same `sentinel_data` package |
| Gold serving | Not decided. The Databricks pipeline is implemented in code (Asset Bundle, Bronze and Silver jobs), but Gold on Databricks is meant for historical analytics, so the read path at request time is open |
| Dispute record | Relational store, engine not decided (SQLite and PostgreSQL are candidates) |
| LLM | Hybrid router; model per route not decided |
| Identity and secrets | Identity provider; Azure Key Vault |
| Serving | Azure Container Apps, autoscaled |
| Observability | Centralised logs and traces, alerts by country |

## Repository layout

```mermaid
flowchart TB
    repo[("One public repository")]
    repo --> data["sentinel-data-engine/<br/>medallion pipeline"]
    repo --> core["sentinel-ai-core/<br/>FastAPI process: chat, orchestrator,<br/>policy, tools, observability, eval"]
    repo --> docs["docs/ · team/ · openspec/"]
    repo --> evidence["evidence/<br/>frozen measurement and evaluation runs"]
    repo --> branding["branding/<br/>styles for chat, docs, slides"]

    classDef comp fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef store fill:#fbfaff,stroke:#3d8bff,stroke-width:2px,color:#1a1530
    class data,core,docs,evidence,branding comp
    class repo store
```

Two code folders. Components are folders, not services: no second HTTP service for the model and no separate web package. Owners and progress per folder are in the team plan.

## References

- Specification of every contract and rule: [Architecture Specification](specification.md)
- Pipeline detail: [data area](../build/areas/data.md), [`sentinel-data-engine/`](../../sentinel-data-engine/README.md)
- Learned component: [decision 007](../build/decisions/007-learned-component.md), [ML area](../build/areas/ml.md)
- Why this flow: [flow selection](../build/flows/03-flow-selection.md), [decision 003](../build/decisions/003-disputes-flow.md), [decision 008](../build/decisions/008-account-inquiry-scope.md)
- Stack decisions: [001](../build/decisions/001-azure-platform.md), [005](../build/decisions/005-backend.md), [006](../build/decisions/006-frontend.md); open ones in [pending decisions](../../team/pending-decisions.md)
- Owners and progress: [folders](../../team/plan.md#folders)
