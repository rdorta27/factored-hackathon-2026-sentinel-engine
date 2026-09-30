# Tasks

Who does what and by when, per day. When you pick a task, add your name; when you finish it, mark it. If it covers a requirement, cite its `REQ-####` and update its status in the [requirements](../docs/requirements/requirements.md).

**States:** Pending, In progress, Done.

## Summary

Daily goals and milestones live in the [plan schedule](plan.md#schedule). The flow is transaction disputes, entered through an account inquiry ([decision 003](../docs/build/decisions/003-disputes-flow.md)).

| Day | Milestone | Tasks |
|---|---|---|
| Mon 9/28 | Decisions recorded; first data measurements | [See](#mon-928) |
| Tue 9/29 | Flow confirmed; architecture reviewed (skeleton not reached) | [See](#tue-929) |
| Wed 9/30 | The skeleton answers end to end; one case works fully | [See](#wed-930) |
| Thu 10/1 | 3 cases in es-419 and pt-BR, public link | [See](#thu-101) |
| Fri 10/2 | Code and results frozen | [See](#fri-102) |
| Sat 10/3 to Mon 10/5 | Presentation and video done; submitted | [See](#sat-103-to-mon-105) |

## Mon 9/28

| Task | Owner | Status |
|---|---|---|
| Record your preference in [pending decisions](pending-decisions.md) | Everyone | Pending |
| Confirm S3 credentials work for all 3 (Natalia already tested them; Rubén verified 9/28: bucket listing OK) | Felix, Rubén | Done |
| Enable the commit hook: `git config core.hooksPath .githooks` | Felix, Natalia | Pending |
| Push the ingestion script to the repo, no credentials: read from `.env` | Natalia | In progress: delivered as Bronze ingestion in `sentinel-data-engine/`; the bucket name in its README is to be removed |
| Document data source, format and partitions in the [dataset](../docs/understand/dataset.md) | Natalia | Pending |
| Decide who provides the Azure subscription, with spend cap and alerts | Unassigned | Pending |
| First look at the data: table inventory vs the dictionary | Rubén | In progress |
| Measure dispute volume for unrecognized charges (`case_type = Claim` + category) and its weight in `contact_reason` | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| Measure what % of dispute-related complaints has a valid `origin_interaction_id` and what % of those interactions has a transcript | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| Profile candidate labels: `category` / `subcategory` and `was_escalated` (balance, consistency, template-like or not) | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| Keyword baseline for dispute category, with a time-based split | Unassigned | Pending |
| List `complaints` opening vs outcome fields to avoid data leakage | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |

## Tue 9/29

| Task | Owner | Status |
|---|---|---|
| Review [decision 003](../docs/build/decisions/003-disputes-flow.md): confirm the disputes flow or switch to cards, and set thresholds | Team | Done: disputes confirmed 9/29 ([flow selection](../docs/build/flows/03-flow-selection.md)) |
| Pick the learned component | Team | Done: prompted LLM, 9/29 ([decision 007](../docs/build/decisions/007-learned-component.md)) |
| Architecture: system, demo and specification | Rubén | Done: [architecture](../docs/architecture/README.md), PR #9 |
| Scope of the account inquiry | Rubén | Done: [decision 008](../docs/build/decisions/008-account-inquiry-scope.md) |
| Minimal pipeline: ingestion, deduplication and quality checks | Natalia | In progress: Bronze, Silver and Gold code with tests in `sentinel-data-engine/`; not yet validated end to end |
| Analysis backing the flow: contact reasons, demand and data quality | Rubén | Done: [flow selection](../docs/build/flows/03-flow-selection.md) |

Not reached on Tuesday and moved to Wednesday: the backend skeleton, the chat, the handoff schema, the held-out design and the Portuguese source.

## Wed 9/30

| Task | Owner | Status |
|---|---|---|
| Backend skeleton: orchestrator, policy engine and 4 mock tools with the [contracts](../docs/architecture/specification.md#tool-contracts) (open dispute idempotent) | Rubén, Felix | In progress: loop, policy engine and in-memory fakes in `sentinel-ai-core/`; handoff is not a tool yet; chat is not connected |
| Simple chat with a test session and conversation state, connected to `POST /chat` | Felix | Done: chat page, test session, `POST /chat` and confirm box verified end to end (web session to case `D-1` + `test_full_turn_is_replayable_by_trace_id`) |
| Synthetic policy configuration per country (MX, CO, AR), placeholder thresholds for decisions 25–27 | Rubén | Done: `sentinel-ai-core/config/policy/` |
| JSON handoff schema (request, verified facts, actions, evidence, open questions, language, country) | Rubén | Pending |
| Gold view with only the [data contract](../docs/architecture/specification.md#data-contract) columns, no personal data | Natalia | Pending |
| Evidence run `2024Q4-v4` recording claim categories and subcategories with counts | Natalia, Rubén | Pending |
| Design the held-out set: labels (from the v4 category list), locales | Rubén | Pending |
| Define the source and reviewer of the Portuguese test cases (decision 15) | Rubén | Pending |
| Look for a justified external source of pt-BR complaints (license, no PII) | Unassigned | Pending |
| Normal case end to end with real data | Rubén, Felix | Pending |
| Action verification: the dispute exists after creation | Rubén | Pending |
| Handoff integrated into the flow | Rubén | Pending |
| Few-shot LLM classifier vs keyword/TF-IDF and zero-shot baselines, with cost and latency | Rubén | Pending |
| First evaluation cases (JSONL) | Rubén | Pending |

## Thu 10/1

| Task | Owner | Status |
|---|---|---|
| Ambiguous and human cases | Unassigned | Pending |
| Decide advisor queue + role landing + admin scope (pending decision 29): implement, JSON-only, or counts-only | Rubén | Pending |
| PII review of the advisor summary before any queue UI (REQ-0047, REQ-0008) | Rubén | Pending |
| Start the video script | Rubén | Pending |
| Outline the presentation: structure and sources of the 4 to 6 slides, no results yet | Rubén | Pending |
| Portuguese | Unassigned | Pending |
| Failure handling: down tools, expired session, bounded retries | Rubén | Pending |
| Structured confirmation: confirm box and `confirmation_token` ([confirmation](../docs/architecture/specification.md#confirmation)) | Felix, Rubén | Pending |
| Structured logs with `trace_id`, latency, tokens and cost ([observability](../docs/architecture/specification.md#observability)) | Rubén | Done: `app/observability/` records + JSONL writer wired from `step()` and `/chat`, audit migrated off cleartext PII, acceptance test green (branch `feature/structured-log`) |
| Charge lookup on Gold, or the fixture if the read path is not up (declared) | Natalia, Rubén | Pending |
| Adversarial set: prompt injection and unauthorized access | Felix | Done: 29 attacks in `tests/adversarial/`, measured `0/29` unsafe (`evidence/adversarial/20260930T214744Z/summary.json`); PII free-text `A9` stays `no_defense_yet` (REQ-0021, REQ-0047) |
| Public link: Azure, or the free-host fallback of decision 13 | Felix | Pending |

## Fri 10/2

| Task | Owner | Status |
|---|---|---|
| Evaluation runner and held-out metrics (safe resolution, unsafe outcomes, handoff, latency, cost) | Rubén | Pending |
| Metrics by language and country, cost per resolution, frozen in `evidence/` | Natalia | Pending |
| Failure analysis and limitations | Unassigned | Pending |
| Sizing: disputes per day and prototype capacity (REQ-0053) | Natalia | Pending |
| Path to production write-up (REQ-0052) | Rubén | In progress: [specification](../docs/architecture/specification.md#path-to-production) |
| Final README update: results and limitations | Rubén | Pending |
| Review the repo for secrets and data; freeze the code | Unassigned | Pending |
| Retire sentinel-login/ once ai-core runs the demo alone (cleanup change, only with ai-core E2E green and the migration change archived) | Rubén | Pending |
| Validate the presentation outline with the group | Rubén, team | Pending |

## Sat 10/3 to Mon 10/5

| Task | Owner | Status |
|---|---|---|
| Review and complete the presentation (4 to 6 slides) with the frozen results, from Friday on | Rubén | Pending |
| Record and edit the video (3 minutes at most) | Rubén | Pending |
| Critical fixes only | Team | Pending |
| Submission, with an internal deadline well before Mon 11:59 pm (UTC-5) | Unassigned | Pending |

## To find out

Need information, not a decision. Ordered by date.

| Question | Who finds out | By when | Status |
|---|---|---|---|
| What format and partitions does the S3 data have? | Natalia | Sun 9/27 | In progress |
| Are there published data terms of use? (the brief mentions them) | Hackathon help channel | Mon 9/28 | Pending |
| What does the "public\*" asterisk mean? Must the repo be public from the start? | Hackathon help channel | Mon 9/28 | Pending |
| Do the terms of use allow copying S3 data to Azure (ADLS)? | Hackathon help channel | Mon 9/28 | Pending |
| How much does Databricks cost (SQL Warehouse and, if used, the Llama endpoint) running 10/1 to 10/5? | Natalia | Mon 9/28 | Done: USD 20-58 total, within the trial credit |
| Deadline on Monday 10/5 and max video length | Hackathon help channel | Mon 9/28 | Done: 11:59 pm (UTC-5); video 3 minutes at most |
| Is the Azure OpenAI model we want available in our region? | Whoever provides the subscription | Mon 9/28 | Pending |
| Are there several monthly snapshots? How was `is_repeat_complainer` computed? | Data area | With the data sample | In progress: one snapshot, `last_updated` up to 2027; `is_repeat_complainer` still open |
| How many late arrivals (gap between `process_date` and `transaction_date`)? | Data area | With the data sample | Done: ~25% of rows are one day late ([dataset](../docs/understand/dataset.md#measured-issues-q4-2024)) |
| Where does the 90-day dispute window come from (regulation, card network, or assumption)? | Natalia | Tue 9/29 | Pending |
| How do we build reference labels (which cases need a human)? | ML area | Tue 9/29 | Pending |
| Cost assumptions (LLM price, advisor cost) | Analysis area | Thu 10/1 | Pending |

## Done

| Task | Owner | Date |
|---|---|---|
| S3 data access tested | Natalia | Sun 9/27 |
| Write access to the repository for Felix and Natalia | Rubén | Sun 9/27 |
| Full team in the hackathon channel | Team | Sun 9/27 |
| Repository created | Rubén | Sun 9/27 |
| Team name: Sentinel Engine | Team | Sun 9/27 |
| Analysis of the challenge documents (datathon kickoff and hackathon brief); commit on Sunday | Rubén | Sat 9/26 |
| Session-bound charge lookup (`GET /transactions` + `lookup_transactions`) with isolation, currency and canary tests | Felix | Wed 9/30 |
| Adversarial set: 29 attacks measured, `0/29` unsafe, frozen in [evidence](../evidence/adversarial/20260930T214744Z/summary.json) | Felix | Wed 9/30 |
