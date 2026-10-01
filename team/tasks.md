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
| Push the ingestion script to the repo, no credentials: read from `.env` | Natalia | Done: Bronze ingestion in `sentinel-data-engine/`; the bucket name is read from `.env` and no longer in the tree (older commits still have it, see the secrets review on Fri) |
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
| Backend skeleton: orchestrator, policy engine and 4 mock tools with the [contracts](../docs/architecture/specification.md#tool-contracts) (open dispute idempotent) | Rubén, Felix | Done: loop, policy engine and tools in `sentinel-ai-core/` (cases now in SQLite); handoff is an outcome filed as a ticket; chat connected |
| Simple chat with a test session and conversation state, connected to `POST /chat` | Felix | Done: chat page, test session and confirm box verified end to end; the route is now `POST /api/v1/chat` (web session to a verified case + `test_full_turn_is_replayable_by_trace_id`) |
| Synthetic policy configuration per country (MX, CO, AR), placeholder thresholds for decisions 25–27 | Rubén | Done: `sentinel-ai-core/config/policy/`; reference percentiles frozen in `evidence/evaluation/2024Q4-v1/summary.json`, thresholds still provisional |
| JSON handoff schema (request, verified facts, actions, evidence, open questions, language, country) | Rubén | Done: the package carries request, summary, per-turn conversation, verified facts, every attempted action, evidence, open questions, language and country; no `customer_id`, no raw text; filed as a ticket (`tests/test_handoff_package.py`) |
| Gold view with only the [data contract](../docs/architecture/specification.md#data-contract) columns, no personal data | Natalia | Done: the pipeline writes `v_service_dispute_eligible_transactions` without names or credit score (`sentinel-data-engine/src/sentinel_data/gold/build_gold.py`); it keeps `is_fraud` and segment, which the service does not read |
| Evidence run recording claim categories and subcategories with counts | Natalia, Rubén | Done: `evidence/evaluation/2024Q4-v1/summary.json` (10 Claim combos, full counter) + derived `sentinel-ai-core/eval/labels.json` |
| Design the held-out set: labels (from the v4 category list), locales | Rubén | Done: dev/held_out splits with no shared ids in `sentinel-ai-core/eval/cases/` |
| Define the source and reviewer of the Portuguese test cases (decision 15) | Rubén | Done (source): 13 team-written pt-BR cases declared simulation; reviewer still open (decision 15) |
| Look for a justified external source of pt-BR complaints (license, no PII) | Unassigned | Dropped: covered by team-written cases; reopen only if decision 15 requires it |
| Normal case end to end with real data | Rubén, Felix | In progress: verified end to end on the mock Gold store; real data waits on the Gold read (Thu, DuckDB adapter) |
| Action verification: the dispute exists after creation | Rubén | Done: read-back verification with `lookup_dispute` and `verify` record |
| Handoff integrated into the flow | Rubén | Done: out-of-scope, person-insist and failure paths hand off with reason keys |
| Prompted LLM router vs keyword baseline, with cost and latency | Rubén | Done (mirrored fixtures, delta zero by construction): `openspec/specs/llm-router/spec.md`; live-model comparison pending decision 10 |
| First evaluation cases (JSONL) | Rubén | Done: 35 cases in `sentinel-ai-core/eval/cases/` |

## Thu 10/1

| Task | Owner | Status |
|---|---|---|
| Ambiguous and human cases | Rubén | Done: missing/person/out-of-scope cases in `sentinel-ai-core/eval/cases/` replayed green |
| Decide advisor queue + role landing + admin scope (pending decision 29): implement, JSON-only, or counts-only | Rubén | Done: [009](../docs/build/decisions/009-demo-ui-and-advisor-view.md), read-only advisor view, no admin panel |
| PII review of the advisor summary before any queue UI (REQ-0047, REQ-0008) | Rubén | Done: package has no names, no raw text, no unverified references; advisor sees customer id and country only (`tests/test_handoffs_api.py`, `tests/test_handoff_package.py`) |
| Start the video script | Rubén | Pending |
| Outline the presentation: structure and sources of the 4 to 6 slides, no results yet | Rubén | Pending |
| Portuguese | Rubén | Done: 13 team-written pt-BR cases; router detection covered in `tests/test_ai_router.py` |
| Failure handling: down tools, expired session, bounded retries | Rubén | Done: `ModelUnavailable` fallback plus runner fault injection, all degrading safely |
| Structured confirmation: confirm box and `confirmation_token` ([confirmation](../docs/architecture/specification.md#confirmation)) | Felix, Rubén | Done: confirm box verified end to end; token stays server-side, never rendered |
| Structured logs with `trace_id`, latency, tokens and cost ([observability](../docs/architecture/specification.md#observability)) | Rubén | Done: `app/observability/` records + JSONL writer wired from `step()` and `POST /api/v1/chat`, audit migrated off cleartext PII, acceptance test green; `var/` anchored to the package |
| Charge lookup on Gold, or the fixture if the read path is not up (declared) | Natalia, Rubén | In progress: DuckDB adapter behind `GoldTransactions` with fallback to the labelled mock (`app/tools/gold_duckdb.py`, `tests/test_gold_duckdb.py`); not yet run on local Gold data |
| Adversarial set: prompt injection and unauthorized access | Felix | Done: 36 attacks in `tests/adversarial/` (chat, disputes API, advisor endpoint), `0/36` unsafe (`evidence/adversarial/20261001T130342Z/summary.json`); PII free-text `A9` stays `no_defense_yet` (REQ-0021, REQ-0047) |
| Public link: Azure, or the free-host fallback of decision 13 | Felix | Pending |
| Integrate PR #20 and align one API: one app at `app.main:app`, everything under `/api/v1`, typed chat replies the page renders | Natalia (Rubén integrated) | Done: `tests/test_contract.py`; OpenSpec change `align-canonical-api-v1` |
| Persist sessions, conversation and cases in SQLite (mentor feedback); delete conversation on logout and expiry | Natalia (Rubén integrated) | Done: `tests/test_state_sqlite.py`; OpenSpec change `persist-state-and-dispute-api` |
| Two-step disputes API and one open dispute per charge across sessions | Natalia, Felix (Rubén integrated) | Done: `tests/test_disputes_api.py`, adversarial B9, B10, C6, D6, D7 |
| Handoff ticket with conversation summary and every attempted action | Natalia (Rubén integrated; summary and attempted actions added by Rubén) | Done: `tests/test_handoff_package.py` |
| Advisor view, role landing and roles in code; `sentinel-login/` backend removed | Felix (Rubén integrated) | Done: `tests/test_handoffs_api.py`, adversarial B11, B12; [009](../docs/build/decisions/009-demo-ui-and-advisor-view.md) |
| Test that no reply shows amounts or merchants outside the verified facts | Rubén | Done: `tests/test_facts_grounding.py` (mutation-checked) |
| A person request while a confirm box is pending must escalate like any other (REQ-0040) | Unassigned | Pending |
| Serve the prompted router in the demo when decision 10 lands (today the served model is the keyword baseline) | Rubén | Pending |
| Fraud and high-amount thresholds (decisions 25, 26) in a separate branch, with a mock row or eval case per rule | Rubén | Pending |
| Tell Felix and Natalia: `sentinel-login/` retired, PR #20 routers replaced by the single API, Gold eligibility uses `CURRENT_DATE` | Rubén | Pending |
| Archive the OpenSpec changes `align-canonical-api-v1`, `persist-state-and-dispute-api`, `serve-demo-ui-with-advisor-view` after the merge | Rubén | Pending |

## Fri 10/2

| Task | Owner | Status |
|---|---|---|
| Evaluation runner and held-out metrics (safe resolution, unsafe outcomes, handoff, latency, cost) | Rubén | Done early 9/30; latest frozen run `evidence/evaluation-runs/2024Q4-eval-v5/` on the aligned API (0 failures, same metrics as v1 except latency) |
| Metrics by language and country, cost per resolution, frozen in `evidence/` | Natalia, Rubén | Done: by-locale/by-country metrics with small-sample limits in the frozen run; cost per resolution "not defined" (no resolutions by design) |
| Failure analysis and limitations | Unassigned | Pending |
| Sizing: disputes per day and prototype capacity (REQ-0053) | Natalia | Pending |
| Path to production write-up (REQ-0052) | Rubén | In progress: [specification](../docs/architecture/specification.md#path-to-production) |
| Final README update: results and limitations | Rubén | Pending |
| Review the repo for secrets and data; freeze the code | Unassigned | Pending |
| Retire sentinel-login/ once ai-core runs the demo alone (cleanup change, only with ai-core E2E green and the migration change archived) | Rubén | Done: backend, tests and packaging removed; only the original page remains as a reference ([009](../docs/build/decisions/009-demo-ui-and-advisor-view.md)) |
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
| How do we build reference labels (which cases need a human)? | ML area | Tue 9/29 | Done: team-written simulation cases (`requires_handoff` marks human cases) plus frozen data labels in `evidence/evaluation/2024Q4-v1/summary.json` |
| Cost assumptions (LLM price, advisor cost) | Analysis area | Thu 10/1 | In progress: measured fixture cost per turn in the frozen run; advisor cost and live-model prices still open (decision 10) |

## Done

| Task | Owner | Date |
|---|---|---|
| S3 data access tested | Natalia | Sun 9/27 |
| Write access to the repository for Felix and Natalia | Rubén | Sun 9/27 |
| Full team in the hackathon channel | Team | Sun 9/27 |
| Repository created | Rubén | Sun 9/27 |
| Team name: Sentinel Engine | Team | Sun 9/27 |
| Analysis of the challenge documents (datathon kickoff and hackathon brief); commit on Sunday | Rubén | Sat 9/26 |
| Session-bound charge lookup (`GET /transactions`, now `GET /api/v1/transactions`, + `lookup_transactions`) with isolation, currency and canary tests | Felix | Wed 9/30 |
| Adversarial set: 29 attacks measured, `0/29` unsafe, frozen in [evidence](../evidence/adversarial/20260930T214744Z/summary.json) | Felix | Wed 9/30 |
| Prompted LLM router with route table, fixtures and safe fallback (`openspec/specs/llm-router/spec.md`, change archived) | Rubén | Wed 9/30 |
| Evaluation evidence frozen: label universe, mix and thresholds (`evidence/evaluation/2024Q4-v1/`, change archived) | Rubén | Wed 9/30 |
| Evaluation runner frozen: bench + system replay, 0 failures, unsafe `0/35` (`evidence/evaluation-runs/2024Q4-eval-v1/`, change archived) | Rubén | Wed 9/30 |
| Runtime `var/` anchored to the app package (`SENTINEL_VAR_DIR` override); stale root `var/` removed | Rubén | Wed 9/30 |
| One app and one API under `/api/v1`; PR #20 integrated | Natalia (Rubén integrated) | Thu 10/1 |
| Sessions, conversation and cases in SQLite with retention | Natalia (Rubén integrated) | Thu 10/1 |
| Disputes API, handoff tickets with summary, advisor view and roles | Natalia, Felix (Rubén integrated) | Thu 10/1 |
| Adversarial set at 36 attacks, `0/36` unsafe ([evidence](../evidence/adversarial/20261001T130342Z/summary.json)) | Rubén, Felix | Thu 10/1 |
