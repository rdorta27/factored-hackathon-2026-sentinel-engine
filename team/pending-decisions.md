# Pending decisions

Open choices, each with its options, supporting material and deadline. The list works with or without a meeting.

## How we decide

1. Read the supporting material and record your preference in your column, or in the team channel.
2. If we agree, it is decided. If not, we settle it in the channel or on a short call.
3. If we still disagree by the deadline, the area owner decides; anything outside an area goes by majority.
4. We record the outcome, then remove the row from the open lists:
   - product and technical decisions in [decisions](../docs/build/decisions/), one file each, using the [template](../docs/build/decisions/_template.md);
   - team decisions in the [plan](plan.md#decisions-made) and in the [decided](#decided) table below.

## Still open from Monday 9/28

These no longer block the skeleton. Most urgent: **16**, because deployment is on Thursday.

| # | Decision | Options or proposal | Supporting material | Felix | Natalia | Rubén |
|---|---|---|---|---|---|---|
| 16 | Azure subscription or credits | Who provides it, with a spend cap and alerts. Only needed for the minimal deployment behind the public link: cloud is not mandatory (help channel, 9/28). Cost assumption: USD 20–58, within the USD 200 trial credit (Natalia's estimate) | [Decision 001](../docs/build/decisions/001-azure-platform.md) | | | |
| 22 | Git submodules | One repo is decided. Open: whether that repo uses git submodules | [Architecture and roadmap](../docs/build/architecture-roadmap.md#repository-layout) | | | |

## Due before submission (Monday 10/5)

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 23 | `team/` in the submission | The repo stays public (decided). Open: keep `team/` in the submission or remove it before submitting. Does not block the skeleton | [Security](../docs/build/security.md#public-repository-and-deployment) |

## Due Tuesday 9/29 (flow review)

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 3 | Demo scope | Which actions the assistant performs (look up, open a dispute, hand off…) and which it does not | [Conversation](../docs/build/conversation.md) |
| 10 | Hybrid LLM models | The router is decided; which model serves each route is not. Natalia's proposal: Llama 3 on Databricks for frequent queries, GPT-4o for ambiguous cases, Portuguese and evaluation | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 12 | Data storage and pipeline | a) local DuckDB · b) Databricks with Bronze, Silver and Gold in Delta Lake on ADLS, queried through SQL Warehouse (Natalia's proposal) · c) Bronze, Silver and Gold with local DuckDB. Until then, the pipeline starts locally with the same layers. Recommendation: a or c for the prototype, with Databricks as the documented production path, since cloud is not mandatory (help channel, 9/28) | [Dataset](../docs/understand/dataset.md), [data area](../docs/build/areas/data.md) |
| 13 | Azure services | A minimal deployment for the public link (Container Apps or App Service) and secrets (Key Vault). With option b of decision 12, also ADLS, Databricks and Unity Catalog | [Decision 001](../docs/build/decisions/001-azure-platform.md) |
| 15 | Portuguese test cases | Translated, synthetic or written by someone who reads Portuguese. The dataset is Spanish-only, so we also need a reviewer. New option: external pt-BR complaint data, allowed if justified (help channel, 9/28): source, license, no PII, labeled as external | [Conversation: languages](../docs/build/conversation.md#languages) |

## Due Wednesday 9/30

| # | Decision | Options or proposal | Supporting material |
|---|---|---|---|
| 14 | Experiment tracking | MLflow (built into Databricks with option b of decision 12), Azure ML or another tool | [ML](../docs/build/areas/ml.md) |

## Decided

| # | Decision | Outcome | Date |
|---|---|---|---|
| 2 | Learned component | Prompted LLM that classifies the dispute category, against a keyword baseline and the same LLM zero-shot, on team-written es-419 and pt-BR text declared as simulation ([007](../docs/build/decisions/007-learned-component.md)) | 9/29 |
| 4 | Owners per area | Natalia: data and data analysis · Rubén: AI, architecture and ML · Felix: full-stack | 9/28 |
| 5 | Daily sync | No meeting. Slack is enough if we talk every day. A status, if needed, goes in the channel at the end of the day | 9/28 |
| 9 | Backend | Python + FastAPI decided; loop tool (LangGraph or plain Python) deferred. Policy, session and idempotency stay in code | 9/28 |
| 11 | Frontend | One-page chat served by FastAPI. Streamlit and Gradio are out. Node only if Felix asks for the video | 9/28 |
| 20 | Video and slides | Rubén. Script starts Thursday 10/1. Slides: Rubén; outline on Thursday 10/1, validated by the group on Friday 10/2, reviewed from Friday to Monday with the results; frozen Monday 10/5 | 9/29 |
| 6 | Task tool | [tasks.md](tasks.md) in the repo. Follow-up is in the team channel; Rubén reviews what is still pending | 9/29 |
| 7 | Code flow | Each person works on a branch, pushes it, and asks in Slack for authorization to merge. Any other teammate can authorize. The author merges. No direct push to `main` | 9/29 |
| 8 | Milestone meetings | No standing meetings. Tasks are assigned as they come up. A meeting, individual or with the group, happens only when needed | 9/29 |
| 1 | Flow | Transaction disputes, entered through an account inquiry. Confirmed against the measurements | 9/29 |
| 21 | Repositories | One public repo. Git submodules are decision 22 | 9/29 |
| 17 | Repository visibility | Public from the start, and it stays public | 9/28 |
| 18 | OpenSpec spec language | English, since specs are submitted | 9/28 |
| 19 | Language of `docs/` and `team/` | Everything in English, including folder and file names | 9/28 |
