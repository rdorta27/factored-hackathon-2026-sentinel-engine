# Team plan

Sentinel Engine · Factored AI & Data Hackathon 2026 · Submission: **Monday 10/5** (time to be confirmed)

> We start on Monday 9/28. Day tasks live in [tasks](tasks.md) and open choices in [pending decisions](pending-decisions.md).

## Schedule

Tentative: we adjust it if anything slips.

| Day | Date | Goal | Milestone |
|---|---|---|---|
| Sun | 9/27 | Prepare: data access, repository, readings | Everyone has access |
| Mon | 9/28 | **Decide** flow, stack, owners and working method. First look at the data | Decisions recorded |
| Tue | 9/29 | Skeleton: 2-3 mock tools, orchestrator, simple chat, minimal pipeline. Analysis backing the flow | **The skeleton answers end to end** |
| Wed | 9/30 | Normal case with real data, JSON handoff, learned component vs baseline. Presentation and video script | **One case works fully** |
| Thu | 10/1 | Ambiguous and human cases, Portuguese, adversarial set, deployment. P1 if time allows | **3 cases in ES and PT, public link** |
| Fri | 10/2 | Held-out evaluation and metrics. Presentation, video, README in English, limitations; review the repo for secrets. Freeze code at night | **Ready to submit** |
| Sat to Mon | 10/3 to 10/5 | Buffer: corrections only. Early submission | **Submitted** |

We want **everything ready by Friday 10/2** and keep the weekend as buffer. Working first: if anything optional blocks a mandatory item, it waits. Priorities live in the [requirements](../docs/requirements/requirements.md).

## Decisions made

| Decision | Status | Record |
|---|---|---|
| Team name: Sentinel Engine | Accepted | — |
| Platform: Microsoft Azure | Accepted | [001](../docs/build/decisions/001-azure-platform.md) |
| Specs with OpenSpec | Accepted | [002](../docs/build/decisions/002-openspec.md) |
| Owners: Natalia, data and data analysis · Rubén, AI, architecture and ML · Felix, full-stack | Accepted | — |
| Hybrid LLM with a router across models (models chosen on Tuesday) | Accepted | — |
| Infrastructure budget: Natalia's estimate (USD 20-58, within the USD 200 Azure trial credit) as the working assumption | Accepted | — |
| Initial flow: transaction disputes, until the Tuesday 9/29 review | Proposed | [003](../docs/build/decisions/003-disputes-flow.md) |
| Repository language: everything in English, including `docs/` and `team/` (decision 19, closed 9/28) | Accepted | [pending decisions](pending-decisions.md) |

Product and technical decisions go in [decisions](../docs/build/decisions/), one file per decision. Team decisions (working method, owners) are recorded here.

## Working method

| Topic | How we work |
|---|---|
| Communication | Everything in the team channel. Challenge questions go to the hackathon help channel |
| Daily sync | 15 min or a channel message: what I did, what I will do, what blocks me. Format and time: decision 5 |
| Tasks | In [tasks](tasks.md), with owner, date and status |
| Specs | With OpenSpec: we propose each change before implementing and cite its requirements |
| Code | Proposal: branch per task and PR reviewed by someone else; `main` always works. Decision 7 pending |
| Decisions | Product and technical ones in [decisions](../docs/build/decisions/); team ones here. We announce all of them in the channel |
| Progress | When a task closes, we update its status in the [requirements](../docs/requirements/requirements.md) |
| Repository | Single repo (`factored-hackathon-2026-sentinel-engine`), private while we work and public at the end |

Two hackathon rules are non-negotiable: no secrets or data in the repo (credentials go in `.env` and are shared by direct message), and the submission is in English.

## Mocks

We start with well-documented mocks and swap them for the real thing one by one, without touching their contracts. Works for any flow.

- **Tue 9/29, skeleton:** 2-3 in-memory mock tools with fixed contracts: 1-2 read tools (e.g. customer data or their transactions), 1 action tool (open a dispute or block a card) and the handoff. Simple chat and Understand → Decide → Act → Verify → Escalate orchestrator. Policy lives in code and the JSON handoff exists from the skeleton: the LLM understands, drafts and picks which tool to call, but never decides permissions or confirms actions.
- **When we swap each mock:** when the schedule milestone asks for it, without changing the contract.
  - Wed 9/30, normal case: reads move to the chosen storage (decision 12; proposal: DuckDB), with declared freshness. The action asks for explicit confirmation.
  - Thu 10/1, ambiguous and human cases, plus deployment: bounded retries, idempotent action and pipeline with partitions, watermark and deduplication.
  - Whatever we do not reach stays a mock and we report it under limitations.
- **Rule:** every mock documents its contract and limitations, as the brief asks (Data and execution boundaries): REQ-0004 (safe tools), REQ-0007 (permissions in code), REQ-0032 (documented mocks).
- **Learned component:** where today a fixed rule stands, we keep it as the baseline and compare it with the component on the same held-out set (REQ-0016).
