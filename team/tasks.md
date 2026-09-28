# Tasks

Who does what and by when, per day. When you pick a task, add your name; when you finish it, mark it. If it covers a requirement, cite its `REQ-####` and update its status in the [requirements](../docs/requirements/requirements.md).

**States:** Pending, In progress, Done.

## Summary

Daily goals and milestones live in the [plan schedule](plan.md#schedule). We work with the transaction-disputes flow until the Tuesday review ([decision 003](../docs/build/decisions/003-disputes-flow.md)).

| Day | Milestone | Tasks |
|---|---|---|
| Mon 9/28 | Decisions recorded; first data measurements | [See](#mon-928) |
| Tue 9/29 | Flow confirmed; the skeleton answers end to end | [See](#tue-929) |
| Wed 9/30 | One case works fully | [See](#wed-930) |
| Thu 10/1 | 3 cases in ES and PT, public link | [See](#thu-101) |
| Fri 10/2 | Ready to submit | [See](#fri-102) |
| Sat 10/3 to Mon 10/5 | Submitted | [See](#sat-103-to-mon-105) |

## Mon 9/28

| Task | Owner | Status |
|---|---|---|
| Record your preference in [pending decisions](pending-decisions.md) | Everyone | Pending |
| Confirm S3 credentials work for all 3 (Natalia already tested them) | Felix, Rubén | In progress |
| Enable the commit hook: `git config core.hooksPath .githooks` | Felix, Natalia | Pending |
| Push the ingestion script (`scripts/ingest_s3_data.py`) to the repo, no credentials: read from `.env` | Natalia | Pending |
| Document data source, format and partitions in the [dataset](../docs/understand/dataset.md) | Natalia | Pending |
| Decide who provides the Azure subscription, with spend cap and alerts | Unassigned | Pending |
| First look at the data: table inventory vs the dictionary | Unassigned | Pending |
| Measure claim volume for unrecognized charges (`case_type = Claim` + category) and its weight in `contact_reason` | Unassigned | Pending |
| Measure what % of dispute-related complaints has a valid `origin_interaction_id` and what % of those interactions has a transcript | Unassigned | Pending |
| Profile candidate labels: `category` / `subcategory` and `was_escalated` (balance, consistency, template-like or not) | Unassigned | Pending |
| Keyword baseline for dispute category, with a time-based split | Unassigned | Pending |
| List `complaints` opening vs outcome fields to avoid data leakage | Unassigned | Pending |

## Tue 9/29

| Task | Owner | Status |
|---|---|---|
| Review [decision 003](../docs/build/decisions/003-disputes-flow.md): confirm the disputes flow or switch to cards, and set thresholds | Team | Pending |
| Pick the learned component (decision 2) | Team | Pending |
| JSON handoff schema (request, verified facts, transactions, actions, evidence, open questions, reason) | Unassigned | Pending |
| Define the source and reviewer of the Portuguese test cases (decision 15) | Unassigned | Pending |
| Backend skeleton: orchestrator and 4 mock tools with fixed contracts (open dispute idempotent) | Unassigned | Pending |
| Simple chat with login and session, connected to the backend | Unassigned | Pending |
| Minimal pipeline: ingestion, deduplication and quality checks | Unassigned | Pending |
| Analysis backing the flow: contact reasons, demand and data quality | Unassigned | Pending |

## Wed 9/30

| Task | Owner | Status |
|---|---|---|
| Normal case end to end with real data | Unassigned | Pending |
| Action verification: the dispute exists after creation | Unassigned | Pending |
| Handoff integrated into the flow | Unassigned | Pending |
| Learned component vs baseline | Unassigned | Pending |
| First evaluation cases | Unassigned | Pending |
| Start the presentation and video script | Unassigned | Pending |

## Thu 10/1

| Task | Owner | Status |
|---|---|---|
| Ambiguous and human cases | Unassigned | Pending |
| Portuguese | Unassigned | Pending |
| Failure handling: down tools, expired session, bounded retries | Unassigned | Pending |
| Adversarial set: prompt injection and unauthorized access | Unassigned | Pending |
| Azure deployment with public link | Unassigned | Pending |

## Fri 10/2

| Task | Owner | Status |
|---|---|---|
| Held-out evaluation and metrics (success, unsafe outcomes, handoff, latency, cost) | Unassigned | Pending |
| Failure analysis and limitations | Unassigned | Pending |
| README in English, presentation and video | Unassigned | Pending |
| Review the repo for secrets and data; freeze the code | Unassigned | Pending |

## Sat 10/3 to Mon 10/5

| Task | Owner | Status |
|---|---|---|
| Critical fixes only | Team | Pending |
| Submission | Unassigned | Pending |

## To find out

Need information, not a decision. Ordered by date.

| Question | Who finds out | By when | Status |
|---|---|---|---|
| What format and partitions does the S3 data have? | Natalia | Sun 9/27 | In progress |
| Are there published data terms of use? (the brief mentions them) | Hackathon help channel | Mon 9/28 | Pending |
| What does the "public\*" asterisk mean? Must the repo be public from the start? | Hackathon help channel | Mon 9/28 | Pending |
| Do the terms of use allow copying S3 data to Azure (ADLS)? | Hackathon help channel | Mon 9/28 | Pending |
| How much does Databricks cost (SQL Warehouse and, if used, the Llama endpoint) running 10/1 to 10/5? | Natalia | Mon 9/28 | Done: USD 20-58 total, within the trial credit |
| Deadline on Monday 10/5 and max video length | Hackathon help channel | Mon 9/28 | Pending |
| Is the Azure OpenAI model we want available in our region? | Whoever provides the subscription | Mon 9/28 | Pending |
| Are there several monthly snapshots? How was `is_repeat_complainer` computed? | Data area | With the data sample | Pending |
| How many late arrivals (gap between `process_date` and `transaction_date`)? | Data area | With the data sample | Pending |
| Where does the 90-day dispute window come from (regulation, card network, or assumption)? | Natalia | Tue 9/29 | Pending |
| How do we build reference labels (which cases need a human)? | ML area | Tue 9/29 | Pending |
| Cost assumptions (LLM price, agent cost) | Analysis area | Thu 10/1 | Pending |

## Done

| Task | Owner | Date |
|---|---|---|
| S3 data access tested | Natalia | Sun 9/27 |
| Write access to the repository for Felix and Natalia | Rubén | Sun 9/27 |
| Full team in the hackathon channel | Team | Sun 9/27 |
| Repository created | Rubén | Sun 9/27 |
| Team name: Sentinel Engine | Team | Sun 9/27 |
| Analysis of the challenge documents (datathon kickoff and hackathon brief); commit on Sunday | Rubén | Sat 9/26 |
