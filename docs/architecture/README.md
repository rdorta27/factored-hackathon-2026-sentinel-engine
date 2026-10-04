# Architecture

| Page | What it answers |
|---|---|
| [System Architecture](system-architecture.md) | The target: layers, components, a case end to end, the learned component, stack, repository layout |
| [Demo Architecture](demo-architecture.md) | The same page for the hackathon submission, with the mocked components marked |
| [What is real](what-is-real.md) | Which parts are real, mocks, synthetic or team-generated, and which numbers are simulations or projections |
| [Architecture Specification](specification.md) | Contracts and rules: tools, confirmation, policy, personal data, failure handling, observability, evaluation, operations |

> **AI understands; code executes and verifies.**

Slide 2 is the picture below; slide 5 is the [mocked components](demo-architecture.md#mocked-components).

```mermaid
flowchart LR
    client(["Customer"]) <--> chat["One page · /api/v1<br/>same process"]
    chat --> session["Session*<br/>and conversation state"]
    session --> orch["Orchestrator<br/>Understand → Decide → Act<br/>→ Verify → Escalate"]
    orch --> tools["Four tools<br/>session-bound"]
    s3[("S3 raw data")] --> pipe["Bronze → Silver → Gold<br/>sentinel-data-engine"] --> gold[("Gold")]
    tools -- "read charges" --> gold
    tools -- "open · read back" --> disputes[("Case store*<br/>disputes · handoff tickets")]
    disputes -- "GET /api/v1/handoffs" --> advisor(["Advisor*<br/>read-only view"])

    classDef comp fill:#f1edff,stroke:#6d4aff,stroke-width:2px,color:#1a1530
    classDef store fill:#fbfaff,stroke:#3d8bff,stroke-width:2px,color:#1a1530
    classDef ext fill:#ffffff,stroke:#a09cb5,stroke-width:1px,color:#3d3a4f
    class chat,session,orch,tools,pipe comp
    class s3,gold,disputes store
    class client,advisor ext
```

The picture is the target system. **\*** In the demo these parts are mocks with the same contract: a trusted test session, a SQLite case store instead of PostgreSQL, and a demo advisor user. Full list: [mocked components](demo-architecture.md#mocked-components).

Legend: violet = component, blue = data store, grey = outside the system. Colours follow [`branding/`](../../branding/BRANDING.md). The picture is the design, not progress; progress is in the [component status](../../team/component-status.md). **Status on 10/1:** every component in the picture runs in `sentinel-ai-core/`; the pipeline exists in `sentinel-data-engine/` but has not fed the service end to end, and there is no public deployment yet.

Key properties:

- **One process.** FastAPI serves the page and the API. No second app; the advisor reads tickets in a read-only view of the same page ([009](../build/decisions/009-demo-ui-and-advisor-view.md)).
- **Session-bound tools.** The LLM never sees or chooses `customer_id`.
- **Verified actions only.** A case number is given after the dispute is read back; a timeout is not success.
- **Mocks keep the contract.** Each mock has the same contract as the real component, so moving to production replaces a backend, not code.
