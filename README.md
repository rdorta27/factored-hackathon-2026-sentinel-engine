---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Sentinel Engine

Factored AI & Data Hackathon 2026 · Submission: **Monday, October 5, 11:59 pm (UTC-5)**

Sentinel Engine is a customer-service assistant for transaction disputes at a bank in México, Colombia and Argentina. It is a prototype. The [requirements coverage](#requirements-coverage) below gives the status of each requirement.

**Live demo:** `https://sentinel-engine.ambitiousmoss-1416426d.eastus.azurecontainerapps.io`. It runs on Azure Container Apps with labelled mock data and `router_v2` (a prompted GLM 5.3 Flash). The keyword baseline answers a turn when the model fails. One replica runs until the awards ([019](docs/build/decisions/019-azure-container-apps.md)). The live revision is from 2026-10-03. It keeps its state on an Azure Files share. It does not have PRs #55 to #57 yet; the final redeploy comes before the video.

**Start here:** [what is real and what is not](docs/architecture/what-is-real.md) · [evidence index](evidence/README.md) · [rationale](docs/rationale/README.md) · [metrics report](docs/build/metrics-report.md)

## What we are building

An assistant, not only a chatbot. It understands the customer and answers only with verified data. It opens a dispute when the customer does not recognize a charge. It confirms that the dispute exists. It hands the case to a person when necessary. It works in **Spanish and Portuguese**.

The guiding principle: **AI understands; code executes and verifies.** The loop is the one that the hackathon asks for: Understand → Decide → Act → Verify → Escalate. Policy, confirmations and the session are in code. The model never sees the customer identifiers.

The system has two layers and a human in the loop:

- **Data:** a Delta Lakehouse. S3 raw data → Bronze → Silver → Gold. DuckDB runs it locally and Azure Databricks runs it in production. Both use the same `sentinel_data` package.
- **Service:** one FastAPI process with the page, the orchestrator, the policy engine and four session-bound tools. It has one API under `/api/v1`: `auth`, `transactions`, `chat`, `disputes` (two steps), `handoffs` (advisor) and `health`.
  - Sessions, conversation state, disputes and handoff tickets are in SQLite. A restart keeps them.
  - Gold comes from the PII-free view in the DuckDB file of the pipeline when the file is present. Otherwise it comes from the labelled mock.
  - Fraud and high-amount handoffs use synthetic thresholds per account country and currency. A bank replaces them in configuration.
  - Code masks personal identifiers in the customer text before any model call.
  - The service uses `router_v2`, a prompted LLM that only labels the intent, when a model is configured. It uses the keyword baseline otherwise and on any model failure. Both are behind one model port.
  - Before the model call, code refuses a request to reveal the prompt and records injection attempts. Code narrows the list of charges with the words of the customer. A "why?" gets its answer from the stored policy decision.
- **Human in the loop:** each handoff becomes a ticket with the reason, a summary of the conversation, the verified facts and every action that the system tried. The advisor reads it in a read-only view of the same page, with the trace of each step.

The submission runs the same code with documented mocks: a test session, SQLite instead of PostgreSQL, a demo advisor user and a synthetic policy. The [mocks](docs/architecture/mocks.md) page explains each mock and why the public link keeps the Gold mock. The [what is real](docs/architecture/what-is-real.md) page lists each mock, each data source and the type of each number.

## Headline results

All numbers are **simulation** on team-written cases, not production measurements ([what is real](docs/architecture/what-is-real.md#numbers)). Each row cites a field of a frozen `summary.json`.

| Result | Baseline | `router_v2` | Field |
|---|---|---|---|
| Intent accuracy, sealed held-out set (n = 280) | 0.5393 | 0.9821 | [eval-v7](evidence/evaluation-runs/2024Q4-eval-v7/summary.json): `component.versions.<version>.breakdown.overall.accuracy` |
| Model latency p50 / p95 (ms) | code only | 1079 / 4475 | `component.versions.router_v2.latency_ms` |
| Safe automated resolution, mock store (n = 56) | 16 | 16 | [resolution-v2](evidence/evaluation-runs/2024Q4-resolution-v2/summary.json): `system.<version>.safe_resolution.resolved` |
| Unsafe outcomes, resolution set | 0/56 | 0/56 | `system.<version>.unsafe_outcomes.rate` |
| Cost per successful resolution (USD) | 0 | 0.000561 | `system.<version>.cost_usd.per_resolution` |
| Unsafe outcomes, adversarial suite | 0/42 | | [adversarial](evidence/adversarial/20261002T222323Z/summary.json): `totals.unsafe_outcome_rate` |

The [metrics report](docs/build/metrics-report.md) gives the intervals, the breakdown by language and country, and the limits.

## Quickstart

Install and run the service (Python 3.12 or newer, from the repository root):

```bash
cd sentinel-ai-core
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app
```

Without a model, the service uses the keyword baseline. To use the measured router:

1. Copy `.env.example` to `.env`.
2. Fill in the `SENTINEL_LLM_*` values ([`.env.example`](.env.example), [secrets guide](sentinel-ai-core/README.md)).
3. Load the file: `set -a; source ../.env; set +a`.
4. Start `uvicorn` again. `GET /api/v1/health` shows the active model.

To publish to Azure, read [`deploy/azure/README.md`](deploy/azure/README.md).

Open `http://localhost:8000/ui` and log in with a test customer: `CUST-0001`, `CUST-0002` or `CUST-0003`, password `Testpass-001`. These credentials are false and for tests only.

To see the advisor side, start the service with the demo roles. Log in as `ADV-0001` (password `Advisor-001`) after a customer asks for a person two times:

```bash
cd sentinel-ai-core
SENTINEL_DEMO_AUTH=1 uvicorn app.main:app
```

The state is in `sentinel-ai-core/var/sentinel.db` (gitignored). Delete it for a clean demo.

To see the structured turn log during a chat (from the repository root):

```bash
tail -f sentinel-ai-core/var/turns.jsonl
```

Run the checks of the workflow. They need no model keys, no cloud credentials and write no evidence:

```bash
cd sentinel-ai-core
pip install -e ".[dev]"
SENTINEL_WRITE_EVIDENCE=0 python3 -m pytest -q

cd ../sentinel-data-engine
pip install -e ".[dev]"
python3 -m pytest -q
```

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs both on each push and pull request.

To replay a frozen evaluation run offline, read the [evidence index](evidence/README.md#evaluation-runs). On 2026-10-04, `2024Q4-resolution-v1`, `2024Q4-resolution-v2` and `2024Q4-calibration-v1` matched their frozen summaries. The system block of `2024Q4-eval-v7` does not reproduce, for the reason in the [metrics report](docs/build/metrics-report.md#9-reproduction).

The data pipeline is in [`sentinel-data-engine/`](sentinel-data-engine/README.md). Sync the raw tables from the organizer bucket into `data/raw/` with the credentials in its `.env`. Then build `data/gold_bank.duckdb` with one command (both gitignored; see its quickstart). The [inventory](docs/data_inventory.md) lists the data sources.

## Requirements coverage

| Priority | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| P0 | 41 | 34 | 5 | 2 | 83% |
| P1 | 12 | 11 | 0 | 1 | 92% |
| P2 | 4 | 1 | 0 | 3 | 25% |
| **Total** | **57** | 46 | 5 | 6 | 81% |

| Status | Requirements |
|---|---|
| **Done** | **Conversation and safety:** REQ-0001 context · REQ-0002 clarify or abstain · REQ-0003 verified records only · REQ-0004 safe simulated tools · REQ-0005 verified actions · REQ-0006 answer, confirm or escalate · REQ-0007 permissions in code · REQ-0008 structured handoff · REQ-0033 policy decides · REQ-0040 request for a person · REQ-0048 decision order. **Demo:** REQ-0009 normal case · REQ-0010 ambiguous case · REQ-0011 human case · REQ-0012 Spanish and Portuguese · REQ-0038 frontend · REQ-0039 freshness · REQ-0041 original currency · REQ-0042 candidates · REQ-0043 status check. **ML:** REQ-0016 learned component against baseline ([eval-v7](evidence/evaluation-runs/2024Q4-eval-v7/summary.json)) · REQ-0017 valid labels, sealed and measured once · REQ-0019 experiment tracking · REQ-0020 same held-out set. **Metrics and analysis:** REQ-0014 flow analysis · REQ-0022 metrics with n · REQ-0024 breakdown by variant and country · REQ-0050 country monitoring · REQ-0053 sizing · REQ-0055 outcome metrics ([resolution-v2](evidence/evaluation-runs/2024Q4-resolution-v2/summary.json)) · REQ-0057 ROI as a projection. **Operations:** REQ-0021 failure tests ([adversarial](evidence/adversarial/20261002T222323Z/summary.json)) · REQ-0025 observability · REQ-0026 retries and idempotency · REQ-0027 session, isolation, retention · REQ-0028 reproducible setup · REQ-0029 explanations from rules and logs · REQ-0032 documented mocks · REQ-0047 no personal data to the model · REQ-0049 country as configuration. **Data:** REQ-0015 pipeline with contracts · REQ-0018 incremental processing · REQ-0031 sources labelled by origin · REQ-0054 no external data. **Delivery:** REQ-0034 clean repository · REQ-0035 live link |
| **In progress** | REQ-0013 and REQ-0030 limits on the slides and a README roadmap · REQ-0051 language check · REQ-0052 path to production (alerts by country) · REQ-0056 trade-offs in the presentation |
| **Pending** | REQ-0036 slides · REQ-0037 video · optional: REQ-0023 LLM judge (not used), REQ-0044 local terms, REQ-0045 app-error context, REQ-0046 handoff routing |

The [requirements](docs/requirements/requirements.md#status-by-priority) page gives the status per requirement and per type, with the evidence of each one.

## Limitations

What the prototype does not do (REQ-0013, REQ-0030). The [sizing](docs/sizing-capacity.md) gives the capacity limits.

- **Mocks:** the submission runs documented mocks: a test session, SQLite instead of PostgreSQL, a demo advisor user, a synthetic policy, a stand-in model in the test suite, and a labelled Gold mock on the public link. Each mock keeps the production contract, so production replaces a backend, not code. The [mocks](docs/architecture/mocks.md) page gives the reason, the limit and the production backend of each one.
- **Data:** synthetic and in Spanish only. Accounts are only in México, Colombia and Argentina, and Mexican accounts are only in USD. The data cannot support a charge investigation: the balance has no usable as-of date, complaints cannot be tied to a charge, blocked products have no transactions, and no customer signal adds to `fraud_score` ([investigation data support](docs/rationale/investigation-data-support.md)). A `fraud_score` above 30 is always fraud, which is an artefact of the data generator. Real Gold runs locally only. The public link uses the labelled mock.
- **Policy:** the dispute window is a declared demonstration policy (`synthetic: true`), not the rule of a bank. One 90-day window serves the three countries. The sources disagree: Argentina counts 30 days from the receipt of the statement, and we found no fixed window for Colombia. The engine cannot express a different window start per country, provisional credit or a response time ([021](docs/build/decisions/021-dispute-policy-sources.md)). The "why?" answer states that the rule is a demonstration policy.
- **Languages:** the Portuguese (`pt-BR`) cases are model-written. No native speaker reviewed them, and the variants are not strictly equivalent ([018](docs/build/decisions/018-evaluation-acceptance.md)). A second model back-translated the three demo lines. A Colombian teammate accepted the es-CO lines. A model, not a speaker, checked the Mexican and Argentine lines. The dataset transcripts are two Spanish templates, not customer language ([evidence](evidence/transcript-chats/20261002T144836Z/summary.json)).
- **Model:** the measured router is more accurate than the keyword baseline on the sealed set ([eval-v7](evidence/evaluation-runs/2024Q4-eval-v7/summary.json), [metrics report](docs/build/metrics-report.md)). A turn that falls back to the baseline has the accuracy of the baseline, and the turn log marks it. The model classifies a greeting alone as out of scope; the sealed set has no such case. The chat answers it with an offer and hands off on the third such turn in a row. The confidence cut-offs ([calibration-v1](evidence/evaluation-runs/2024Q4-calibration-v1/summary.json)) are descriptive (validation n = 26) and off by default.
- **State:** SQLite and one replica. Login-attempt and write-rate counters are per process. PostgreSQL is the path to more than one instance.
- **Privacy:** code masks free customer text by pattern before the model call. It does not detect personal data outside those patterns.
- **Safety evidence:** 42 attacks with `0/42` unsafe outcomes ([adversarial run](evidence/adversarial/20261002T222323Z/summary.json)). Three injection attempts pass only because the stand-in model is the keyword baseline. The attack block of `eval-v7` tests attacks against the live model. Zero unsafe outcomes on a small set does not prove zero risk.
- **Resolution:** a simulation over the mock store only. [`2024Q4-resolution-v2`](evidence/evaluation-runs/2024Q4-resolution-v2/summary.json) resolves the same eligible cases for the baseline and `router_v2`, with no unsafe outcome and no missed handoff. It is not a field resolution rate: the set uses only the charges in the mock store, and it has no pending charge ([022](docs/build/decisions/022-resolution-acceptance.md)).
- **Capacity:** no load test of `/api/v1/chat` exists. The requests per second of one replica are not measured.
- **Monitoring and ROI:** country monitoring uses a replayed, simulated workload ([evidence](evidence/monitoring/2024Q4-resolution-v2-replay/summary.json)). No field log exists. The ROI is a break-even projection with an assumed advisor cost, not a measured saving ([roi](docs/build/roi.md)).

## Reading guide

1. **[The challenge](docs/understand/overview.md):** what we must build, how the judges score it and what we submit.
2. **[Architecture](docs/architecture/README.md):** the target system, the demo with its mocks, and the specification.
3. **[What is real](docs/architecture/what-is-real.md):** real, mock, synthetic, team-generated, simulation or projection, for each part.
4. **[Flow selection](docs/build/flows/03-flow-selection.md):** why transaction disputes, with data and reproducible measurements.
5. **[Rationale](docs/rationale/README.md):** why each main choice, with its evidence and the slide sentence.
6. **[Evidence](evidence/README.md):** every frozen run, its status and its data type.

The [documentation index](docs/README.md) covers everything else.

## Repository map

| Path | What it holds |
|---|---|
| [`sentinel-data-engine/`](sentinel-data-engine/README.md) | Medallion pipeline (S3 → Bronze → Silver → Gold) on Delta Lake. DuckDB locally. The Databricks mode is implemented and not deployed. 13 LATAM Bank tables, about 19 M records. |
| [`sentinel-ai-core/`](sentinel-ai-core/) | The service: FastAPI with one API under `/api/v1`, the policy engine, the orchestrator and the chat UI. State in SQLite. A DuckDB Gold adapter with a fallback to the labelled mock. The served `router_v2` with a baseline fallback. The evaluation harness (`eval/`): development cases, the sealed held-out set and the multi-turn resolution set. Owners are in [team/plan.md](team/plan.md#folders). |
| [`sentinel-login/`](sentinel-login/README.md) | The original demo page, kept as a reference. It is not a backend and the service does not serve it ([009](docs/build/decisions/009-demo-ui-and-advisor-view.md)). |
| [`docs/`](docs/README.md) | Architecture, the challenge and the data, requirements, rationale, design rules, decisions and delivery |
| [`evidence/`](evidence/README.md) | Frozen, reproducible runs. The index gives the status and data type of each run. |
| [`deploy/azure/`](deploy/azure/README.md) | The deployment script and its notes |
| [`scripts/`](scripts/) | Repository scripts, for example the generator of the flow measurements page |
| [`team/`](team/) | Plan, tasks and pending decisions |

## Team workflow

Planning is in [`team/`](team/), apart from the project documentation:

- **[Pending decisions](team/pending-decisions.md):** what is still open and when the team must decide it.
- **[Tasks](team/tasks.md):** who does what, and when.
- **[Plan](team/plan.md):** schedule, decisions, working method and mocks.

## Rules

- **No secrets and no data in the repository.** The repository is public. Credentials go in `.env` (gitignored). Teammates share them by direct message.
- **English, in ASD-STE100.** Code and documents are in English, written in simplified technical English. The assistant answers in Spanish and Portuguese.

## For agents

[`AGENTS.md`](AGENTS.md) explains the layout, the language rule and what must never go into a commit.
