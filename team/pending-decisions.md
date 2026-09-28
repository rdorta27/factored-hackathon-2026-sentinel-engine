# Pending decisions

What we still have to decide, with options and supporting material. Works with or without a meeting.

## Method

Proposal:

1. Everyone reads the supporting material and records their preference in their column (or in the channel) before **Monday 9/28**.
2. If we agree, it is decided. If not, we discuss it in the channel or on a short call.
3. If by end of day we still disagree, the area owner decides; everything else by majority.
4. We record each decision: product and technical ones in [decisions](../docs/build/decisions/) (one file per decision, using the [template](../docs/build/decisions/_template.md)); team ones in the [plan](plan.md). Then we remove it from this list.

## Monday 9/28

These block Tuesday's skeleton. Most urgent: **16** (deployment is on Thursday) and **21** (defines how code is organized from the skeleton on).

| # | Decision | Options or proposal | Supporting material | Felix | Natalia | Rubén |
|---|---|---|---|---|---|---|
| 1 | Flow | Proposal: transaction disputes, provisional; we confirm or change it on Tuesday 9/29 with measurable criteria. Alternative: cards | [Decision 003 (proposal)](../docs/build/decisions/003-disputes-flow.md), [flow options](../docs/build/flows/options.md) | | | |
| 2 | Learned component | With the disputes flow: dispute-category classifier (`description` / `customer_text`) vs keywords, or escalation predictor (`was_escalated`) with opening-time features. We pick it in the Tuesday review together with decision 1 | [ML](../docs/build/areas/ml.md), [metrics](../docs/build/metrics.md) | | | |
| 5 | Daily sync | 15-min meeting or channel message; time | | | | |
| 6 | Task tool | Proposal: [tasks.md](tasks.md) in the repo | | | | |
| 7 | Code flow | Mandatory pull request or direct push to `main`; who reviews | | | | |
| 8 | Milestone meetings | When we review together (e.g. Wednesday, Friday and Sunday) | [Schedule](plan.md#schedule) | | | |
| 9 | Backend language and framework | Proposal: Python with FastAPI | [Architecture](../docs/understand/architecture.md#stack) | | | |
| 16 | Azure subscription or credits | Who provides it; spend cap and alerts. Cost assumption: USD 20-58, within the USD 200 trial credit (Natalia's estimate) | [Decision 001](../docs/build/decisions/001-azure-platform.md) | | | |
| 17 | Repository visibility | Private now and public at the end, or public from now (today it is public). Includes whether `team/` stays in the submission or is removed beforehand | [Security](../docs/build/security.md#public-repository-and-deployment) | | | |
| 21 | Repositories | Natalia's proposal: split by domain (data, AI, web and infrastructure). Options: a) single repo with per-domain folders and separate dependencies · b) several repos for development and one for submission · c) submodules. The submission asks for a single public repo | Natalia's proposal (channel, 9/28) | | | |
| 18 | OpenSpec spec language | Proposal: English, because specs are submitted | [Decision 002](../docs/build/decisions/002-openspec.md) | | | |

## Later

| # | Decision | Options or proposal | By when |
|---|---|---|---|
| 10 | Hybrid LLM models | The router is already decided; missing which model goes on each route. Natalia's proposal: Llama 3 on Databricks for frequent queries and GPT-4o for ambiguous cases, Portuguese and evaluation | Tue 9/29 |
| 12 | Data storage and pipeline | a) Local DuckDB · b) Databricks with Bronze, Silver and Gold in Delta Lake on ADLS; the API queries Gold via SQL Warehouse (Natalia's proposal) · c) Bronze, Silver and Gold with local DuckDB. Meanwhile, the pipeline starts local with the same pattern | Tue 9/29 |
| 3 | Demo scope | Which actions the assistant performs (check, block, open a dispute…) and which it does not | Tue 9/29 |
| 11 | Frontend | Simple chat: Streamlit, Gradio or own web (Python or Node; no .NET, we work on Linux) | Tue 9/29 |
| 13 | Azure services | Deployment (Container Apps or App Service), secrets (Key Vault). With option b of decision 12: ADLS, Databricks and Unity Catalog | Tue 9/29 |
| 15 | Portuguese test cases | Translated, synthetic or written by someone who reads Portuguese. The dataset is Spanish-only: also define who reviews them | Tue 9/29 |
| 20 | Who makes the presentation and video | The script starts on Wednesday | Tue 9/29 |
| 14 | Experiment tracking | MLflow (included in Databricks if option b of decision 12 is picked), Azure ML or other | Wed 9/30 |
| 19 | Language of `docs/` in the submission | Decided 9/28: translate everything to English (this change). Recorded in [plan](plan.md); REQ-0051 updated to English-only | Done |

## Decided

| # | Decision | Outcome | Date |
|---|---|---|---|
| 19 | Language of `docs/` and `team/` | Translate everything to English, including folder and file names; close the old Spanish-working-copy rule | 9/28 |
