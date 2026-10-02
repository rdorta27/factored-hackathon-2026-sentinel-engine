# Pending decisions

Open choices, each with its options, supporting material and deadline. The list works with or without a meeting.

## How we decide

1. Read the supporting material and record your preference in your column, or in the team channel.
2. If we agree, it is decided. If not, we settle it in the channel or on a short call.
3. If we still disagree by the deadline, the area owner decides; anything outside an area goes by majority.
4. We record the outcome, then remove the row from the open lists:
   - product and technical decisions in [decisions](../docs/build/decisions/), one file each, using the [template](../docs/build/decisions/_template.md);
   - team decisions in the [plan](plan.md#decisions-made) and in the [decided](#decided) table below.

## Open

None. New choices are added here with their options, supporting material and deadline.

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
| 29 | Advisor queue, admin panel, role landing | Role landing and a read-only advisor view of escalated tickets (`GET /api/v1/handoffs`) in the ai-core page; demo advisor only with `SENTINEL_DEMO_AUTH=1`; admin panel out; `sentinel-login/` backend removed ([009](../docs/build/decisions/009-demo-ui-and-advisor-view.md)) | 10/1 |
| 25 | Suspected-fraud handoff rule | Claim (`fraud.claim`) or score above the p95 per account country and currency (`fraud.score`), synthetic values from evidence 2024Q4-v2 ([010](../docs/build/decisions/010-fraud-handoff-rule.md)) | 10/1 |
| 26 | High-amount handoff threshold | p95 per account country and charge currency, synthetic values from evidence 2024Q4-v2; Mexican MXN has none ([011](../docs/build/decisions/011-high-amount-threshold.md)) | 10/1 |
| 13, 16 | Deployment and subscription | Azure Container Apps, one Docker container, inside the free grant and the trial credit; decided for the submission on 10/2 after Hugging Face dropped its free Docker tier ([019](../docs/build/decisions/019-azure-container-apps.md), superseding [012](../docs/build/decisions/012-public-deployment.md)) | 10/2 |
| 14 | Experiment tracking | The frozen evaluation runs are the tracking record; MLflow on Databricks in production ([013](../docs/build/decisions/013-experiment-tracking.md)) | 10/1 |
| 23 | `team/` in the submission | Kept: it shows the plan, decisions and evidence behind the build; reviewed before submitting | 10/1 |
| 27 | Data staleness threshold | Off in the demo (Gold's age is always zero); per-country threshold in production ([014](../docs/build/decisions/014-data-staleness.md)) | 10/1 |
| 28 | Handoff delivery in production | Ticket store and advisor view in the demo; queue to the bank's CRM in production ([015](../docs/build/decisions/015-handoff-delivery.md)) | 10/1 |
| 10 | Router models | Open-weight models on Fireworks AI, cheap and strong route, chosen per route by a rule fixed before measuring; gpt-oss-120b as the starting cheap model ([016](../docs/build/decisions/016-router-models.md)) | 10/1 |
| 15 | Portuguese | A Portuguese-speaking customer holds an MX, CO or AR account; pt-BR twins of the key cases, written by one model, back-translated to Spanish by another and checked by the team ([017](../docs/build/decisions/017-portuguese.md)) | 10/1 |
