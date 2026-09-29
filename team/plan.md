# Team plan

Sentinel Engine · Factored AI & Data Hackathon 2026 · Submission: **Monday 10/5, 11:59 pm (UTC-5)**

> We start on Monday 9/28. Day tasks live in [tasks](tasks.md) and open choices in [pending decisions](pending-decisions.md).

## Schedule

Tentative: we adjust it if anything slips.

| Day | Date | Goal | Milestone |
|---|---|---|---|
| Sun | 9/27 | Prepare: data access, repository, readings | Everyone has access |
| Mon | 9/28 | **Decide** flow, stack, owners and working method. First look at the data | Decisions recorded |
| Tue | 9/29 | Skeleton: 4 mock tools, orchestrator, simple chat, minimal pipeline. Analysis backing the flow | **The skeleton answers end to end** |
| Wed | 9/30 | Normal case with real data, JSON handoff, learned component vs baseline | **One case works fully** |
| Thu | 10/1 | Ambiguous and human cases, Portuguese, adversarial set, deployment. Video script starts. P1 if time allows | **3 cases in es-419 and pt-BR, public link** |
| Fri | 10/2 | Held-out evaluation and metrics. README in English, limitations; review the repo for secrets. Freeze code at night | **Code and results frozen** |
| Sat to Mon | 10/3 to 10/5 | Presentation and video recording on the frozen build (results from Fri). Critical fixes only. Submit with margin on Mon | **Submitted** |

We want **code, results and README frozen by Friday 10/2**. The presentation and the video are finished over the weekend and Monday 10/5, on top of the frozen build, so the extra days go to building more. Set an internal submission time on Monday, well before 11:59 pm. Working first: if anything optional blocks a mandatory item, it waits. Priorities live in the [requirements](../docs/requirements/requirements.md).

## Decisions made

| Decision | Status | Record |
|---|---|---|
| Team name: Sentinel Engine | Accepted | — |
| Platform: Microsoft Azure | Accepted | [001](../docs/build/decisions/001-azure-platform.md) |
| Specs with OpenSpec, written in English (decision 18) | Accepted | [002](../docs/build/decisions/002-openspec.md) |
| Owners: Natalia, data and data analysis · Rubén, AI, architecture and ML · Felix, full-stack | Accepted | — |
| Hybrid LLM with a router across models (models chosen on Tuesday) | Accepted | — |
| Infrastructure budget: Natalia's estimate (USD 20-58, within the USD 200 Azure trial credit) as the working assumption | Accepted | — |
| Disputes store: SQLite locally, Postgres on Azure, separate from Gold | Accepted | [architecture](../docs/understand/architecture.md#two-layers) |
| No .NET: outside the team's stack (Python, FastAPI). Target is Azure; locally it runs on Linux | Accepted | [architecture](../docs/understand/architecture.md#stack) |
| Flow: transaction disputes, entered through an account inquiry (confirmed 9/29) | Accepted | [003](../docs/build/decisions/003-disputes-flow.md) |
| Repository language: everything in English, including `docs/` and `team/` (decision 19, closed 9/28) | Accepted | [pending decisions](pending-decisions.md) |
| No daily sync meeting. Slack if we talk every day; a status, if needed, at the end of the day (decision 5) | Accepted | [pending decisions](pending-decisions.md) |
| Backend: Python + FastAPI (decision 9); loop tool (LangGraph or plain Python) deferred | Accepted | [005](../docs/build/decisions/005-backend.md) |
| Frontend: one-page chat served by FastAPI; no Streamlit or Gradio (decision 11) | Accepted | [006](../docs/build/decisions/006-frontend.md) |
| Video and slides: Rubén. Script from Thursday 10/1. Group validates the slides Friday 10/2; content finished over the weekend and Monday; frozen Monday 10/5 (decision 20) | Accepted | [delivery](../docs/build/delivery.md) |
| Tasks live in the repo; follow-up is in the team channel. Rubén reviews what is still pending (decision 6) | Accepted | [tasks](tasks.md) |
| Code: branch, push, Slack authorization, author merges. No direct push to `main` (decision 7) | Accepted | [pending decisions](pending-decisions.md) |
| No standing milestone meetings. Ad hoc only (decision 8) | Accepted | [pending decisions](pending-decisions.md) |
| One public repository. Git submodules still open (decision 21) | Accepted | [architecture roadmap](../docs/build/architecture-roadmap.md#repository-layout) |

Product and technical decisions go in [decisions](../docs/build/decisions/), one file per decision. Team decisions (working method, owners) are recorded here.

## Working method

| Topic | How we work |
|---|---|
| Communication | Everything in the team channel. Challenge questions go to the hackathon help channel |
| Status | No standing sync and no standing milestone meetings. We talk on Slack during the day. A meeting, individual or with the group, happens only when a task needs it; the outcome goes in the channel |
| Tasks | In [tasks](tasks.md), with owner, date and status |
| Specs | With OpenSpec: we propose each change before implementing and cite its requirements |
| Code | Branch per change, push, ask in Slack for authorization to merge. Any other teammate can authorize; the author merges. No direct push to `main` |
| Decisions | Product and technical ones in [decisions](../docs/build/decisions/); team ones here. We announce all of them in the channel |
| Progress | When a task closes, we update its status in the [requirements](../docs/requirements/requirements.md) |
| Repository | Single repo (`factored-hackathon-2026-sentinel-engine`), public from the start and it stays public |

Two hackathon rules are non-negotiable: no secrets or data in the repo (credentials go in `.env` and are shared by direct message), and the submission is in English.

## Mocks

We start with well-documented mocks and swap them for the real thing one by one, without touching their contracts. Shown here for the transaction-disputes flow.

- **Tue 9/29, skeleton:** a test session and 4 in-memory mock tools with fixed contracts: look up transactions, open dispute (idempotent from the start, so a retry never duplicates it), look up dispute to verify, and the handoff (see [components and mocks](../docs/understand/architecture.md#components-and-mocks)). Simple chat and Understand → Decide → Act → Verify → Escalate orchestrator. Policy lives in code and the JSON handoff exists from the skeleton: the LLM understands, drafts and picks which tool to call, but never decides permissions or confirms actions.
- **When we swap each mock:** when the schedule milestone asks for it, without changing the contract.
  - Wed 9/30, normal case: reads move to the chosen storage (decision 12: DuckDB or Databricks), with declared freshness. The action asks for explicit confirmation.
  - Thu 10/1, ambiguous and human cases, plus deployment: bounded retries and pipeline with partitions, watermark and deduplication.
  - Whatever we do not reach stays a mock and we report it under limitations.
- **Rule:** every mock documents its contract and limitations, as the brief asks (Data and execution boundaries): REQ-0004 (safe tools), REQ-0007 (permissions in code), REQ-0032 (documented mocks).
- **Learned component:** where today a fixed rule stands, we keep it as the baseline and compare it with the component on the same held-out set (REQ-0016).
