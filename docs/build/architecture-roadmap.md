# Architecture and roadmap

Architecture, personal data (PII) lifecycle and action plan. Source: the data area's proposal (9/28), translated and reconciled with the repository. Anything stated as decided links to its decision or requirement; anything still open carries a callout with its decision number. In the diagrams, dashed grey boxes are proposals not yet built, blue boxes are agreed components and green cylinders are stores.

> Project: Sentinel Engine — Factored AI & Data Hackathon 2026
> Workflow focus: transaction-dispute intake (Spanish & Portuguese), as working hypothesis ([decision 003](decisions/003-disputes-flow.md), provisional until the Tuesday 9/29 review)
> Submission: Monday, October 5 (time to be confirmed)
> Internal goal: everything ready Friday, October 2; the weekend is buffer
> Areas: data and data analysis · AI, architecture and ML · full-stack (owners in the [plan](../../team/plan.md#decisions-made))

## Executive summary

Sentinel Engine is an AI banking assistant that takes in transaction disputes in Mexico, Colombia and Argentina.

**Guiding principle: AI understands; code executes and verifies.** The LLM handles comprehension, intent extraction and multilingual dialogue. Financial decisions, identity authorization, dispute eligibility thresholds and dispute creation are enforced by deterministic code and backend APIs. Same principle as [architecture](../understand/architecture.md#central-principle), which stays the canonical reference for layers and walkthroughs.

## PII lifecycle

PII management spans data engineering, AI engineering and full-stack, across two planes (see [decision 004](decisions/004-pii-lifecycle.md), proposed).

### Plane 1: data at rest (batch / lakehouse) — data area

```mermaid
flowchart LR
    raw[("S3 raw data")] --> bronze["Bronze<br/>as received"] --> silver["Silver<br/>static PII redaction"] --> gold[("Gold<br/>ready for tools and ML")]
    silver --- rules["· hash document numbers<br/>· mask card numbers (**** 1234)<br/>· restrict access to credit score and income<br/>(kept as ML features)<br/>· schema contracts and audit"]

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class raw,gold store
    class bronze,silver proposed
    class rules ext
```

> [!NOTE]
> Proposed, not implemented. Static masking is recorded in [security](security.md#data) as the 9/28 proposal.

### Plane 2: data in flight (real-time chat) — AI and full-stack areas

```mermaid
flowchart TD
    msg(["Customer message<br/>'My DNI is 1098234'"]) --> mask["Stage 1 · masking engine<br/>Regex + NER"]
    mask -- "store encrypted map<br/>TOKEN_ID_1 → 1098234" --> vault[("Token vault<br/>per session, ephemeral")]
    mask -- "anonymized prompt only<br/>'My DNI is [TOKEN_ID_1]'" --> llm["Stage 2 · hybrid LLM router<br/>models: decision 10"]
    llm -- "tool intent + token parameters" --> tools["Stage 3 · deterministic tools<br/>unmask inside the tool"]
    vault -- "unmask token<br/>(compare only, never a lookup key)" --> tools
    session[("Session<br/>customer_id")] -- "lookup key" --> tools
    tools -- "parameterized SQL<br/>WHERE customer_id = session" --> db[("Gold")]
    tools --> ui(["Client UI<br/>response without raw PII"])

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class msg,ui ext
    class mask,llm,tools proposed
    class vault,session,db store
```

> [!NOTE]
> Proposal without implementation yet — no code, tooling undecided (Presidio vs Regex/SpaCy), retention policy pending. Unmasked values are only compared against the session customer's data, never used as lookup keys. Tracked in [decision 004](decisions/004-pii-lifecycle.md).

| Domain | Responsibility | Owner | Tools |
|---|---|---|---|
| Data engineering (at rest) | Static masking and hashing in the Silver layer, so analysts and batch ML never see raw credentials | Natalia | PySpark, Delta Lake column masking, hash functions |
| AI engineering (in flight) | Dynamic prompt masking and unmasking: mask before LLM calls, keep the per-session token vault, unmask inside tool calls | Rubén | Python, Presidio / Regex / SpaCy NER, session token vault |
| Full-stack / backend (session security) | Secure transport and UI rendering: `customer_id` via headers/JWT, no PII in browser logs or client storage | Felix | FastAPI, JWT, HTTPS/TLS |

## System architecture (4 stages)

```mermaid
flowchart TD
    ui(["Customer chat · web UI<br/>Spanish and Portuguese"]) --> l1
    l1["Stage 1 · security and session isolation<br/>PII masking · token vault<br/>authenticated customer_id"] -- "anonymized prompt" --> l2
    l2["Stage 2 · orchestrator and hybrid LLM router<br/>routine queries → light model<br/>ambiguous, pt-BR, evaluation → strong model<br/>(models: decision 10)"] -- "tool intent + token parameters" --> l3
    l3["Stage 3 · deterministic policy and tools<br/>parameterized queries by session<br/>eligibility rules (90-day window, to validate)<br/>handoff package (JSON)"]
    l3 --> l4[("Stage 4 · audit log<br/>append-only, anonymized<br/>MX · CO · AR")]
    l3 -- "read" --> gold[("Gold<br/>backend: decision 12")]
    l3 -- "write · read back" --> disputes[("Disputes store<br/>SQLite · Postgres")]

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class ui ext
    class l1,l2,l3 real
    class l4,gold,disputes store
```

> [!NOTE]
> Stage 2 models are undecided (decision 10, due Tue 9/29). The Gold storage backend is an open question for the data area (decision 12: local DuckDB or Databricks). Disputes are not written to Gold: they go to a separate operational store (SQLite locally, Postgres on Azure), so they can be read back at once to verify them ([architecture](../understand/architecture.md#two-layers)). The >90-day eligibility cutoff is a valid working rule but must be validated against the data ([decision 003](decisions/003-disputes-flow.md)).

## Repository layout

```mermaid
flowchart TD
    d["sentinel-data-engine · data area<br/>Medallion pipelines, static PII masking,<br/>quality checks, schema contracts<br/>PySpark · Delta Lake"]
    a["sentinel-ai-core · AI area<br/>PII masking, LLM router,<br/>deterministic rules<br/>Python · FastAPI · Pydantic"]
    w["sentinel-web-interface · full-stack area<br/>chat UI, handoff view,<br/>session management"]
    infra["sentinel-devops-infra · shared<br/>IaC (Terraform or Bicep) · CI/CD (GitHub Actions)"]
    delivery[("Public submission repo<br/>factored-hackathon-2026-sentinel-engine<br/>who assembles it: decision 21")]
    d & a & w -. "merged into" .-> delivery
    infra -- "builds and deploys" --> delivery

    classDef real fill:#dde3ff,stroke:#5b4fd6,stroke-width:2px,color:#1b1640
    classDef mock fill:#ffe9c7,stroke:#c77d12,stroke-width:2px,stroke-dasharray:6 4,color:#3a2a00
    classDef store fill:#e3f4ea,stroke:#2f8a55,stroke-width:2px,color:#123a22
    classDef proposed fill:#f1f1f4,stroke:#77778a,stroke-width:2px,stroke-dasharray:4 3,color:#26262f
    classDef ext fill:#ffffff,stroke:#77778a,stroke-width:1px,color:#26262f
    class d,a,w,infra proposed
    class delivery store
```

> [!WARNING]
> Pending (decision 21): separate-by-domain repos vs a single repo. The submission requires a single public repository, so if development splits across repos, the delivery repo and who assembles it must be defined before submission. The current repository is a single repo.

## Action plan (deadline Monday 10/5, time TBD)

Per-person view of the [plan schedule](../../team/plan.md#schedule): same dates and milestones, split by owner. If they ever differ, the plan wins.

```mermaid
gantt
    title Sentinel Engine — action plan
    dateFormat YYYY-MM-DD
    axisFormat %a %d/%m
    tickInterval 1day
    todayMarker off
    section Milestones
    Decisions recorded                     :milestone, m1, 2026-09-28, 0d
    Skeleton answers end to end            :milestone, m2, 2026-09-29, 0d
    One case works fully                   :milestone, m3, 2026-09-30, 0d
    3 cases in es-419 and pt-BR, public link      :milestone, m4, 2026-10-01, 0d
    P0 ready, code freeze                  :milestone, m5, 2026-10-02, 0d
    Submission                             :milestone, m6, 2026-10-05, 0d
    section Data (Natalia)
    Ingestion and profiling                :2026-09-28, 1d
    Analysis backing the flow              :2026-09-28, 2d
    Bronze and Silver, PII at rest         :2026-09-29, 1d
    Gold with cutoff date                  :2026-09-30, 1d
    Incremental pipeline                   :2026-10-01, 1d
    Data quality and limitations           :2026-10-02, 1d
    section AI, architecture, ML (Rubén)
    Measurements for the flow review       :2026-09-28, 1d
    Orchestrator, mocks, baseline, PII     :2026-09-29, 1d
    Normal es-419 case, ML vs baseline         :2026-09-30, 1d
    Ambiguous, human, pt-BR, adversarial   :2026-10-01, 1d
    Held-out evaluation and metrics        :2026-10-02, 1d
    section Full-stack (Felix)
    FastAPI, chat and session skeleton     :2026-09-29, 1d
    Confirmation and handoff in the UI     :2026-09-30, 1d
    Azure deployment                       :2026-10-01, 1d
    README                                 :2026-10-02, 1d
    section Team
    Deck and video script                  :2026-09-30, 2d
    Deck and video                         :2026-10-02, 1d
    Buffer, fixes only                     :2026-10-03, 3d
```

Notes:

- The script starts on Wednesday 9/30; deck and video are finished on Friday 10/2, once the held-out results exist. Who makes them is decision 20.
- The weekend is buffer for corrections only, with early submission.
- Portuguese test cases: source and reviewer still to define (decision 15). Vocabulary lives in [glossary.pt-br.md](../understand/glossary/glossary.pt-br.md).
- Submission time and channel are unconfirmed (asked in the hackathon help channel); until confirmed, assume Monday 10/5, end of day.

## Cost matrix (MVP budget)

Working assumption (decision 16: USD 20–58 within the USD 200 trial credit), **pending validation against Azure pricing**.

| Component | Open source / free tier | Paid cloud (Azure / Databricks) | Estimated MVP cost |
|---|---|---|---|
| Compute & API server | FastAPI (local dev) | Azure Container Apps / Web App | USD 0–13 |
| LLM inference | Ollama / vLLM (local Llama 3) | Azure OpenAI (token usage) | USD 10–25 |
| Data lakehouse | DuckDB / local Delta Lake | Azure Databricks (single-node cluster) | USD 10–20 |
| PII & safety | Microsoft Presidio / Regex | Azure AI Content Safety | USD 0–2 |
| Storage & secrets | Local `.env` | ADLS Gen2 + Azure Key Vault | USD 0–2 |
| CI/CD & DevOps | GitHub Actions (free minutes) | GitHub Actions runner | USD 0 |
| **Total** | — | — | **USD 20–58 (covered by USD 200 credit)** |

## Appendix: alignment with the repository

| # | Claim | Repo status |
|---|---|---|
| 1 | Focus: transaction-dispute intake es-419/pt-BR | Working hypothesis, provisional until Tue 9/29 review ([003](decisions/003-disputes-flow.md)) |
| 2 | Guiding principle | Accepted, canonical in [architecture](../understand/architecture.md#central-principle) |
| 3 | Domain owners per area | Accepted ([plan](../../team/plan.md)) |
| 4 | Static masking in Silver | Proposed on 9/28, recorded in [security](security.md#data), not implemented |
| 5 | Dynamic masking: token vault, mask and unmask | Proposed, no code yet ([004](decisions/004-pii-lifecycle.md)) |
| 6 | Hybrid router model choice | Undecided (decision 10, due Tue 9/29) |
| 7 | Storage backend | Open question for the data area (decision 12) |
| 8 | Multi-repo development layout | Pending (decision 21); conflicts with the single-public-repo submission requirement |
| 9 | MVP cost USD 20–58 | Working assumption, pending Azure validation (decision 16) |
| 10 | Deadline Mon 10/5, internal goal Fri 10/2 | Accepted; submission time/channel unconfirmed |
| 11 | Eligibility thresholds (e.g. >90-day cutoff) | Valid working rules, must be validated against data ([003](decisions/003-disputes-flow.md)) |
| 12 | Per-piece stack (Key Vault, Container Apps, frontend) | Proposals under pending decisions 1, 11, 13 |
| 13 | JSON handoff package | Defined ([003](decisions/003-disputes-flow.md), REQ-0008) |
| 14 | Action plan: P0 complete Thu 10/1; held-out, deck and video from Thu 10/1; code freeze, evaluation and video over the weekend | Aligned with the [plan](../../team/plan.md#schedule): P0 and code freeze on Fri 10/2, script from Wed 9/30, held-out on Fri 10/2, weekend as buffer. Added the learned component, adversarial set, frontend and data analysis, which the original plan lacked |
