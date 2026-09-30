# Pending decisions

Open choices, each with its options, supporting material and deadline. The list works with or without a meeting.

## How we decide

1. Read the supporting material and record your preference in your column, or in the team channel.
2. If we agree, it is decided. If not, we settle it in the channel or on a short call.
3. If we still disagree by the deadline, the area owner decides; anything outside an area goes by majority.
4. We record the outcome, then remove the row from the open lists:
   - product and technical decisions in [decisions](../docs/build/decisions/), one file each, using the [template](../docs/build/decisions/_template.md);
   - team decisions in the [plan](plan.md#decisions-made) and in the [decided](#decided) table below.

## Due Wednesday 9/30

Includes the decisions due Tuesday 9/29 that were not settled.

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 10 | Hybrid LLM models | The router is decided; which model serves each route is not. Natalia's proposal: Llama 3 on Databricks for frequent queries, GPT-4o for ambiguous cases, Portuguese and evaluation | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 14 | Experiment tracking | MLflow (built into Databricks, decision 12), Azure ML or another tool | [ML](../docs/build/areas/ml.md) |
| 15 | Portuguese test cases | Translated, synthetic or written by someone who reads Portuguese. The dataset is Spanish-only, so we also need a reviewer. New option: external pt-BR complaint data, allowed if justified (help channel, 9/28): source, license, no PII, labeled as external | [Conversation: languages](../docs/build/conversation.md#languages) |
| 25 | Suspected-fraud handoff rule | Which runtime signal triggers the handoff: (a) the customer states the charge was not theirs; (b) `fraud_score` above a threshold; (c) either. `is_fraud` is excluded: it is a label known after the fact. If (b) or (c), the threshold is chosen on the development split, never on held-out | [Specification: decision priority](../docs/architecture/specification.md#decision-priority), [ML](../docs/build/areas/ml.md) |
| 26 | High-amount handoff threshold | Amount above which a dispute goes to an advisor, per country (MX, CO, AR) in the original currency, as configuration. Proposal: a high percentile of the development-window amounts per country | [Specification: decision priority](../docs/architecture/specification.md#decision-priority) |
| 27 | Data staleness threshold | How old Gold may be before the assistant stops answering from it and offers a handoff. The as-of date is always stated either way (REQ-0039) | [Specification: failure handling](../docs/architecture/specification.md#failure-handling) |

## Due Thursday 10/1

Postponed from 9/28 and 9/29. Until then the demo runs locally; the Azure services it would use are already mocked (test session, `.env`, local logs), but the public link is a mandatory deliverable and cannot be a mock.

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 13 | Azure services | A minimal deployment for the public link (Container Apps or App Service) and secrets (Key Vault). With the Databricks production path of decision 12, also ADLS, Databricks and Unity Catalog. **Fallback if Azure is not ready on Thursday:** deploy the same container on a free host (for example Render, Fly.io or Hugging Face Spaces, Docker) with usage limits, recorded as an exception to [decision 001](../docs/build/decisions/001-azure-platform.md); the brief only requires a minimal deployment (REQ-0035) | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 16 | Azure subscription or credits | Who provides it, with a spend cap and alerts. Only needed for the minimal deployment behind the public link: cloud is not mandatory (help channel, 9/28). Cost assumption: USD 20–58, within the USD 200 trial credit (Natalia's estimate) | [Decision 001](../docs/build/decisions/001-azure-platform.md) |

## Due before submission (Monday 10/5)

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 23 | `team/` in the submission | The repo stays public (decided). Open: keep `team/` in the submission or remove it before submitting. Does not block the skeleton | [Security](../docs/build/security.md#public-repository-and-deployment) |
| 28 | Handoff delivery in production | How the JSON package reaches advisors in production: queue, CRM ticket or similar. Not needed for the demo (the package is returned and logged). Routing by language and specialty is REQ-0046 (P2, simulated). Presented as remaining deployment work | [Specification: path to production](../docs/architecture/specification.md#path-to-production) |
| 29 | Advisor queue, admin panel and role landing (deferred from the chat-session migration) | (a) Implement advisor queue + role landing for the demo; (b) keep JSON-only handoff with no advisor UI; (c) admin counts only, no panel. Depends on PII review of the advisor summary vs REQ-0047/REQ-0008. Owner: Rubén | [Handoff](../docs/architecture/specification.md#tool-contracts), [roles spec](../openspec/specs/roles/spec.md), decision 28 |

## Decided

| # | Decision | Outcome | Date |
|---|---|---|---|
| 1 | Flow | Transaction disputes, entered through an account inquiry. Confirmed against the measurements | 9/29 |
| 2 | Learned component | Prompted LLM that classifies the dispute category, against a keyword baseline and the same LLM zero-shot, on team-written es-419 and pt-BR text declared as simulation ([007](../docs/build/decisions/007-learned-component.md)) | 9/29 |
| 3 | Demo scope | Look up charges and their status, explain, open a dispute after structured confirmation, read it back, hand off. Not in scope: balances, products, cards, credit, deciding fraud or the dispute outcome ([decision 008](../docs/build/decisions/008-account-inquiry-scope.md), [Demo Architecture](../docs/architecture/demo-architecture.md)) | 9/29 |
| 4 | Owners per area | Natalia: data and data analysis · Rubén: AI, architecture and ML · Felix: full-stack | 9/28 |
| 5 | Daily sync | No meeting. Slack is enough if we talk every day. A status, if needed, goes in the channel at the end of the day | 9/28 |
| 6 | Task tool | [tasks.md](tasks.md) in the repo. Follow-up is in the team channel; Rubén reviews what is still pending | 9/29 |
| 7 | Code flow | Each person works on a branch, pushes it, and asks in Slack for authorization to merge. Any other teammate can authorize. The author merges. No direct push to `main` | 9/29 |
| 8 | Milestone meetings | No standing meetings. Tasks are assigned as they come up. A meeting, individual or with the group, happens only when needed | 9/29 |
| 9 | Backend | Python + FastAPI decided; loop tool (LangGraph or plain Python) deferred. Policy, session and idempotency stay in code | 9/28 |
| 11 | Frontend | One-page chat served by FastAPI. Streamlit and Gradio are out. Node only if Felix asks for the video | 9/28 |
| 12 | Data storage and pipeline | Delta Lakehouse: DuckDB with the Delta extension locally, Azure Databricks with PySpark and Delta Lake on ADLS Gen2 in production. Bronze, Silver and Gold live in `sentinel-data-engine/` ([stack](../docs/architecture/system-architecture.md#stack-and-deployment)) | 9/29 |
| 17 | Repository visibility | Public from the start, and it stays public | 9/28 |
| 18 | OpenSpec spec language | English, since specs are submitted | 9/28 |
| 19 | Language of `docs/` and `team/` | Everything in English, including folder and file names | 9/28 |
| 20 | Video and slides | Rubén. Script starts Thursday 10/1. Slides: Rubén; outline on Thursday 10/1, validated by the group on Friday 10/2, reviewed from Friday to Monday with the results; frozen Monday 10/5 | 9/29 |
| 21 | Repositories | One public repo. Git submodules are decision 22 | 9/29 |
| 22 | Git submodules | Not used. The team works by folders in the single repository ([repository layout](../docs/architecture/system-architecture.md#repository-layout)) | 9/29 |
| 24 | Account-inquiry scope | The entry point covers charges and transactions only (what a charge is, its status, whether it can be disputed). Balances, products, cards and credit are out of scope: the assistant says so and offers a handoff. One read tool, `lookup_transactions` ([scope](../docs/architecture/specification.md#scope)) | 9/29 |
