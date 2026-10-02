# Tasks

Who does what and by when, per day. When you pick a task, add your name; when you finish it, mark it. If it covers a requirement, cite its `REQ-####` and update its status in the [requirements](../docs/requirements/requirements.md).

**States:** Pending, In progress, Done. Open tasks live in [open work by priority](#open-work-by-priority); finished ones stay in the day log.

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

## Open work by priority

Every open task, ordered by what the submission needs first. Each one cites the requirement it closes; the order follows the [dependencies between requirements](../docs/requirements/requirements.md#dependencies). The day sections below are the log of what was done.

### Critical: blocks the submission (P0)

| # | Task | REQ | Owner | Due | Unblocks | Status |
|---|---|---|---|---|---|---|
| 1 | Public link on Hugging Face Spaces: `Dockerfile`, Space secrets, demo variables ([012](../docs/build/decisions/012-public-deployment.md)) | REQ-0035 | Felix | Fri 10/2 | Video on the deployed tool (REQ-0037) | Pending |
| 2 | Pipeline quality report: add nulls, orphaned records, late arrivals and Bronze counts for partitioned tables, and explain the drop from the declared volumes | REQ-0015 | Natalia | Fri 10/2 | REQ-0015 done | In progress: end-to-end run and [report](../sentinel-data-engine/data_quality_report.md) exist and reproduce locally |
| 3 | Charge lookup on Gold, or the fixture if the read path is not up (declared) | REQ-0003, REQ-0015 | Natalia, Rubén | Fri 10/2 | Normal case on real data | In progress: the DuckDB adapter reads the view as Delta under `data/gold/`, but the pipeline writes `data/gold_bank.duckdb`; export the view as Delta or point the adapter at the DuckDB file |
| 4 | Normal case end to end with real data | REQ-0009 | Rubén, Felix | Fri 10/2 | Demo on real data | In progress: verified end to end on the mock Gold store; waits on the Gold read |
| 5 | Decide the model per route (decision 10), serve the prompted router, re-record fixtures and freeze a new run id | REQ-0016, REQ-0019 | Rubén | Fri 10/2 | Metrics, trade-offs and slides with a real delta | Pending: the served model is the keyword baseline; delta zero by construction |
| 6 | Define and test how the system serves a Portuguese-speaking customer without Portuguese data: replies, country and currency, reviewed cases (decision 15) | REQ-0012, REQ-0009 | Unassigned | Fri 10/2 | Normal case in Portuguese, the 3 demo cases in pt-BR | Pending |
| 7 | Final metrics report on the frozen run: n, mix, variability, failures, justified splits and thresholds | REQ-0055, REQ-0022, REQ-0017, REQ-0020 | Natalia, Rubén | Fri 10/2 | Trade-offs, slides | Pending |
| 8 | Failure analysis and limitations: no Portuguese in the dataset, only MX, CO and AR, small samples, capacity, deployment, risks | REQ-0013, REQ-0030 | Unassigned | Fri 10/2 | README, slides | Pending |
| 9 | Path to production write-up, including monitoring; handoff delivery decided ([015](../docs/build/decisions/015-handoff-delivery.md)) | REQ-0052 | Rubén | Fri 10/2 | — | In progress: [specification](../docs/architecture/specification.md#path-to-production) |
| 10 | Review the repo for secrets and data, including the bucket id in older commits; freeze the code | REQ-0034 | Felix | Fri 10/2 | Public link, submission | Done: gitleaks over the full history (0 findings) and manual review; bucket name accepted and documented in [security](../docs/build/security.md#history-review-req-0034-101) |
| 11 | Final README update: results and limitations | REQ-0030 | Rubén | Fri 10/2 | — | Pending |
| 12 | Start the video script | REQ-0037 | Rubén | Thu 10/1 | Video | Pending |
| 13 | Outline the presentation: structure and sources of the 4 to 6 slides, no results yet | REQ-0036 | Rubén | Thu 10/1 | Validation Fri | Pending |
| 14 | Validate the presentation outline with the group | REQ-0036 | Rubén, team | Fri 10/2 | Slides | Pending |
| 15 | Review and complete the presentation with the frozen results | REQ-0036, REQ-0056 | Rubén | Mon 10/5 | Submission | Pending |
| 16 | Record and edit the video (3 minutes at most) | REQ-0037 | Rubén | Mon 10/5 | Submission | Pending |
| 17 | Pre-submission language check: README, slides, video script, `docs/`, `team/` | REQ-0051 | Unassigned | Mon 10/5 | Submission | Pending |
| 18 | Submission, with an internal deadline well before Mon 11:59 pm (UTC-5) | — | Unassigned | Mon 10/5 | — | Pending |
| 19 | Critical fixes only after the freeze | — | Team | Sat 10/3 to Mon 10/5 | — | Pending |

### High: scores points once P0 is on track (P1 and team hygiene)

| # | Task | REQ | Owner | Due | Unblocks | Status |
|---|---|---|---|---|---|---|
| 1 | Archive the OpenSpec changes `align-canonical-api-v1`, `persist-state-and-dispute-api`, `serve-demo-ui-with-advisor-view`, and `add-fraud-and-high-amount-rules` after PR #29 merges | — | Rubén | Fri 10/2 | — | Done: all four under `openspec/changes/archive/` (2026-10-01), main specs synced |
| 2 | Enable the commit hook: `git config core.hooksPath .githooks` | — | Felix, Natalia | Fri 10/2 | — | Pending |
| 3 | ROI against the baseline with cost per resolution, labelled as a projection | REQ-0057 | Unassigned | Fri 10/2 | — | Pending |
| 4 | Breakdown by authorized segment and disparity analysis on the frozen run | REQ-0024 | Unassigned | Fri 10/2 | Limitations | Pending |
| 5 | Report by country (latency, failures, escalations) from the JSONL logs | REQ-0050 | Unassigned | Fri 10/2 | Path to production | Pending |
| 6 | Neutral Spanish: apply the glossary and add a case with another country's term | REQ-0044 | Unassigned | Fri 10/2 | — | Pending |
| 7 | Keep `amount_usd` in `silver_transactions` (filled in ~95% of ARS and COP charges, empty by design in USD) for cross-country comparisons | REQ-0024 | Natalia | — | — | Pending |

### Low: only if time remains (P2) or to confirm and close

| # | Task | REQ | Owner | Due | Unblocks | Status |
|---|---|---|---|---|---|---|
| 1 | Close as not applicable if no LLM judge is used | REQ-0023 | Unassigned | Fri 10/2 | — | Pending |
| 2 | Recent app-error context offered as a question | REQ-0045 | Unassigned | — | — | Pending |
| 3 | Simulated handoff routing by language and specialty | REQ-0046 | Unassigned | — | — | Pending |
| 4 | Keyword baseline for dispute category, with a time-based split: confirm whether the served keyword baseline covers it and close | REQ-0016 | Unassigned | — | — | Pending |
| 5 | First look at the data: table inventory vs the dictionary | — | Rubén | — | — | In progress |
| 6 | Record your preference in [pending decisions](pending-decisions.md) | — | Everyone | — | — | Pending |

## Log by day

### Mon 9/28

| Task | Owner | Status |
|---|---|---|
| Confirm S3 credentials work for all 3 (Natalia already tested them; Rubén verified 9/28: bucket listing OK) | Felix, Rubén | Done |
| Push the ingestion script to the repo, no credentials: read from `.env` | Natalia | Done: Bronze ingestion in `sentinel-data-engine/`; the bucket name is read from `.env` and no longer in the tree (older commits still have it, see the secrets review on Fri) |
| Measure dispute volume for unrecognized charges (`case_type = Claim` + category) and its weight in `contact_reason` | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| Measure what % of dispute-related complaints has a valid `origin_interaction_id` and what % of those interactions has a transcript | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| Profile candidate labels: `category` / `subcategory` and `was_escalated` (balance, consistency, template-like or not) | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |
| List `complaints` opening vs outcome fields to avoid data leakage | Rubén | Done: [evidence](../docs/build/flows/02-flow-measurements.md) |

### Tue 9/29

| Task | Owner | Status |
|---|---|---|
| Review [decision 003](../docs/build/decisions/003-disputes-flow.md): confirm the disputes flow or switch to cards, and set thresholds | Team | Done: disputes confirmed 9/29 ([flow selection](../docs/build/flows/03-flow-selection.md)) |
| Pick the learned component | Team | Done: prompted LLM, 9/29 ([decision 007](../docs/build/decisions/007-learned-component.md)) |
| Architecture: system, demo and specification | Rubén | Done: [architecture](../docs/architecture/README.md), PR #9 |
| Scope of the account inquiry | Rubén | Done: [decision 008](../docs/build/decisions/008-account-inquiry-scope.md) |
| Analysis backing the flow: contact reasons, demand and data quality | Rubén | Done: [flow selection](../docs/build/flows/03-flow-selection.md) |

Not reached on Tuesday and moved to Wednesday: the backend skeleton, the chat, the handoff schema, the held-out design and the Portuguese source.

### Wed 9/30

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
| Action verification: the dispute exists after creation | Rubén | Done: read-back verification with `lookup_dispute` and `verify` record |
| Handoff integrated into the flow | Rubén | Done: out-of-scope, person-insist and failure paths hand off with reason keys |
| Prompted LLM router vs keyword baseline, with cost and latency | Rubén | Done (mirrored fixtures, delta zero by construction): `openspec/specs/llm-router/spec.md`; live-model comparison pending decision 10 |
| First evaluation cases (JSONL) | Rubén | Done: 35 cases in `sentinel-ai-core/eval/cases/` |

### Thu 10/1

| Task | Owner | Status |
|---|---|---|
| Ambiguous and human cases | Rubén | Done: missing/person/out-of-scope cases in `sentinel-ai-core/eval/cases/` replayed green |
| Decide advisor queue + role landing + admin scope (pending decision 29): implement, JSON-only, or counts-only | Rubén | Done: [009](../docs/build/decisions/009-demo-ui-and-advisor-view.md), read-only advisor view, no admin panel |
| PII review of the advisor summary before any queue UI (REQ-0047, REQ-0008) | Rubén | Done: package has no names, no raw text, no unverified references; advisor sees customer id and country only (`tests/test_handoffs_api.py`, `tests/test_handoff_package.py`) |
| Portuguese | Rubén | Done (router only): 13 single-turn pt-BR utterances and router detection in `tests/test_ai_router.py`; serving a Portuguese-speaking customer is still open (see open work) |
| Failure handling: down tools, expired session, bounded retries | Rubén | Done: `ModelUnavailable` fallback plus runner fault injection, all degrading safely |
| Structured confirmation: confirm box and `confirmation_token` ([confirmation](../docs/architecture/specification.md#confirmation)) | Felix, Rubén | Done: confirm box verified end to end; token stays server-side, never rendered |
| Structured logs with `trace_id`, latency, tokens and cost ([observability](../docs/architecture/specification.md#observability)) | Rubén | Done: `app/observability/` records + JSONL writer wired from `step()` and `POST /api/v1/chat`, audit migrated off cleartext PII, acceptance test green; `var/` anchored to the package |
| Adversarial set: prompt injection and unauthorized access | Felix | Done: 36 attacks in `tests/adversarial/` (chat, disputes API, advisor endpoint), `0/36` unsafe (`evidence/adversarial/20261001T130342Z/summary.json`); PII free-text `A9` stays `no_defense_yet` (REQ-0021, REQ-0047) |
| Integrate PR #20 and align one API: one app at `app.main:app`, everything under `/api/v1`, typed chat replies the page renders | Natalia (Rubén integrated) | Done: `tests/test_contract.py`; OpenSpec change `align-canonical-api-v1` |
| Persist sessions, conversation and cases in SQLite (mentor feedback); delete conversation on logout and expiry | Natalia (Rubén integrated) | Done: `tests/test_state_sqlite.py`; OpenSpec change `persist-state-and-dispute-api` |
| Two-step disputes API and one open dispute per charge across sessions | Natalia, Felix (Rubén integrated) | Done: `tests/test_disputes_api.py`, adversarial B9, B10, C6, D6, D7 |
| Handoff ticket with conversation summary and every attempted action | Natalia (Rubén integrated; summary and attempted actions added by Rubén) | Done: `tests/test_handoff_package.py` |
| Advisor view, role landing and roles in code; `sentinel-login/` backend removed | Felix (Rubén integrated) | Done: `tests/test_handoffs_api.py`, adversarial B11, B12; [009](../docs/build/decisions/009-demo-ui-and-advisor-view.md) |
| Test that no reply shows amounts or merchants outside the verified facts | Rubén | Done: `tests/test_facts_grounding.py` (mutation-checked) |
| Tell Felix and Natalia: `sentinel-login/` retired, PR #20 routers replaced by the single API, Gold eligibility uses `CURRENT_DATE` | Rubén | Done |
| Fraud and high-amount thresholds per account country and currency (decisions 25, 26) | Rubén | Done: [010](../docs/build/decisions/010-fraud-handoff-rule.md), [011](../docs/build/decisions/011-high-amount-threshold.md); evidence `evidence/evaluation/2024Q4-v2/`, run `2024Q4-eval-v6` |
| Source inventory: every input labeled by origin, no external data ([inventory](../docs/data_inventory.md)) | Natalia | Done: REQ-0031, REQ-0054 |
| Pipeline run end to end on the full dataset with a quality report; Silver normalizes `México`; Gold uses the 2026-06-17 cutoff | Natalia | Done: `data/gold_bank.duckdb` (gitignored), [report](../sentinel-data-engine/data_quality_report.md); quality metrics still incomplete (open task) |
| Labelled incremental fixture: late arrival, duplicate and schema change | Natalia | Done: `sentinel-data-engine/tests/test_incremental_fixture.py` (REQ-0018) |
| Sizing and capacity specification | Natalia | Done: [sizing](../docs/sizing_capacity.md) (REQ-0053) |
| Data setup in two steps: sync the raw tables, build the DuckDB file | Natalia | Done: [quickstart](../sentinel-data-engine/README.md#9-local-development-quickstart) (REQ-0028) |
| Mask personal identifiers in free text before the model | Felix | Done: `app/privacy/`, `tests/privacy/`; adversarial A9 blocked in `evidence/adversarial/20261001T222341Z/summary.json` (REQ-0047) |
| Data findings for thresholds: Mexican accounts are USD only, `Mexico` names purchases in Mexico, Silver drops `amount_usd` | Rubén | Done: [dataset assumptions](../docs/understand/dataset.md#assumptions); asked in the help channel |
| A person request while the confirm box is open escalates like any other; insisting after other messages still escalates; the extra model call is logged | Felix (Rubén reviewed and fixed) | Done: `tests/test_person_while_confirming.py`, PR #30 (REQ-0040) |
| Close pending decisions 13, 14, 16, 23, 27 and 28 | Rubén | Done: [012](../docs/build/decisions/012-public-deployment.md) to [015](../docs/build/decisions/015-handoff-delivery.md) |
| Requirements regrouped by type (frontend and backend, non-functional, data and ML, analytics, delivery) with one card each and their dependencies | Rubén | Done: [requirements](../docs/requirements/requirements.md) |

### Fri 10/2

| Task | Owner | Status |
|---|---|---|
| Evaluation runner and held-out metrics (safe resolution, unsafe outcomes, handoff, latency, cost) | Rubén | Done early 9/30; latest frozen run `evidence/evaluation-runs/2024Q4-eval-v5/` on the aligned API (0 failures, same metrics as v1 except latency) |
| Metrics by language and country, cost per resolution, frozen in `evidence/` | Natalia, Rubén | Done: by-locale/by-country metrics with small-sample limits in the frozen run; cost per resolution "not defined" (no resolutions by design) |
| Retire sentinel-login/ once ai-core runs the demo alone (cleanup change, only with ai-core E2E green and the migration change archived) | Rubén | Done: backend, tests and packaging removed; only the original page remains as a reference ([009](../docs/build/decisions/009-demo-ui-and-advisor-view.md)) |

### Sat 10/3 to Mon 10/5

Nothing done yet; see [open work by priority](#open-work-by-priority).

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
