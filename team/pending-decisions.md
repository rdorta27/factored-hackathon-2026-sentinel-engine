# Pending decisions

Open choices, each with its options, supporting material and deadline. The list works with or without a meeting.

## How we decide

1. Read the supporting material and record your preference in your column, or in the team channel.
2. If we agree, it is decided. If not, we settle it in the channel or on a short call.
3. If we still disagree by the deadline, the area owner decides; anything outside an area goes by majority.
4. We record the outcome, then remove the row from the open lists:
   - product and technical decisions in [decisions](../docs/build/decisions/), one file each, using the [template](../docs/build/decisions/_template.md);
   - team decisions in the [plan](plan.md#decisions-made) and in the [decided](#decided) table below.

## Due today, Monday 9/28

These block Tuesday's skeleton. Most urgent: **16**, because deployment is on Thursday, and **21**, because it shapes how code is organized from the skeleton on.

| # | Decision | Options or proposal | Supporting material | Felix | Natalia | Rubén |
|---|---|---|---|---|---|---|
| 5 | Daily sync | A 15-minute meeting or a channel message; and at what time | | | | |
| 6 | Task tool | Proposal: [tasks.md](tasks.md) in the repo | | | | |
| 7 | Code flow | Mandatory pull request or direct push to `main`; who reviews | | | | |
| 8 | Milestone meetings | When we review together (e.g. Wednesday, Friday and Sunday) | [Schedule](plan.md#schedule) | | | |
| 9 | Backend language and framework | Proposal: Python with FastAPI | [Architecture](../docs/understand/architecture.md#stack) | | | |
| 16 | Azure subscription or credits | Who provides it, with a spend cap and alerts. Only needed for the minimal deployment behind the public link: the mentors confirmed cloud is not mandatory (9/28). Cost assumption: USD 20–58, within the USD 200 trial credit (Natalia's estimate) | [Decision 001](../docs/build/decisions/001-azure-platform.md) | | | |
| 17 | `team/` in the submission | The repo stays public (decided). Open: keep `team/` in the submission or remove it before submitting | [Security](../docs/build/security.md#public-repository-and-deployment) | | | |
| 21 | Repositories | Natalia proposes splitting by domain (data, AI, web, infrastructure). Options: a) one repo with a folder per domain and separate dependencies · b) several repos to develop in, one to submit · c) submodules. The submission requires a single public repo | [Architecture and roadmap](../docs/build/architecture-roadmap.md#repository-layout) | | | |

## Due Tuesday 9/29 (flow review)

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 1 | Flow | Proposal: transaction disputes, confirmed or changed against measurable criteria. Alternative: cards | [Decision 003](../docs/build/decisions/003-disputes-flow.md), [flow options](../docs/build/flows/options.md) |
| 2 | Learned component | Lead candidate: few-shot LLM classifier of the dispute category (examples from the training split only), against keywords or TF-IDF and against the same LLM zero-shot. Works in pt-BR without Portuguese training data. Alternative: escalation predictor (`was_escalated`) with opening-time features. Mentors (9/28): a prompted LLM counts if it is defined, evaluated rigorously and justified | [ML](../docs/build/areas/ml.md), [metrics](../docs/build/metrics.md) |
| 3 | Demo scope | Which actions the assistant performs (look up, open a dispute, hand off…) and which it does not | [Conversation](../docs/build/conversation.md) |
| 10 | Hybrid LLM models | The router is decided; which model serves each route is not. Natalia's proposal: Llama 3 on Databricks for frequent queries, GPT-4o for ambiguous cases, Portuguese and evaluation | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 11 | Frontend | Simple chat: Streamlit, Gradio or our own web app (Python or Node; no .NET, it is outside the team's stack) | [AI area](../docs/build/areas/ai.md) |
| 12 | Data storage and pipeline | a) local DuckDB · b) Databricks with Bronze, Silver and Gold in Delta Lake on ADLS, queried through SQL Warehouse (Natalia's proposal) · c) Bronze, Silver and Gold with local DuckDB. Until then, the pipeline starts locally with the same layers. Recommendation: a or c for the prototype, with Databricks as the documented production path, since cloud is not mandatory (mentors, 9/28) | [Dataset](../docs/understand/dataset.md), [data area](../docs/build/areas/data.md) |
| 13 | Azure services | A minimal deployment for the public link (Container Apps or App Service) and secrets (Key Vault). With option b of decision 12, also ADLS, Databricks and Unity Catalog | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 15 | Portuguese test cases | Translated, synthetic or written by someone who reads Portuguese. The dataset is Spanish-only, so we also need a reviewer. New option: external pt-BR complaint data, allowed if justified (mentors, 9/28): source, license, no PII, labeled as external | [Conversation: languages](../docs/build/conversation.md#languages) |
| 20 | Presentation and video | Who makes them; the script starts on Wednesday | [Delivery](../docs/build/delivery.md) |

## Due Wednesday 9/30

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 14 | Experiment tracking | MLflow (built into Databricks with option b of decision 12), Azure ML or another tool | [ML](../docs/build/areas/ml.md) |

## Decided

| # | Decision | Outcome | Date |
|---|---|---|---|
| 4 | Owners per area | Natalia: data and data analysis · Rubén: AI, architecture and ML · Felix: full-stack | 9/28 |
| 17 | Repository visibility | Public from the start, and it stays public | 9/28 |
| 18 | OpenSpec spec language | English, since specs are submitted | 9/28 |
| 19 | Language of `docs/` and `team/` | Everything in English, including folder and file names | 9/28 |
