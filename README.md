# Sentinel Engine

Factored AI & Data Hackathon 2026 · Submission: **Monday, October 5, 11:59 pm (UTC-5)**

A customer-service assistant for transaction disputes at a bank in Mexico, Colombia and Argentina. Prototype under active development. Status per requirement is tracked in Requirements coverage below; open decisions are marked as such.

**Live demo:** `https://sentinel-engine.ambitiousmoss-1416426d.eastus.azurecontainerapps.io` — Azure Container Apps, labeled mock data and router_v2 (a prompted GLM 5.3 Flash) with the keyword baseline as a per-turn fallback; it runs one replica that stays up until the awards, and sessions do not survive a redeploy or restart ([decision 019](docs/build/decisions/019-azure-container-apps.md)). The deployed image predates PRs #49 and #50 (narrowing, prompt-extraction refusal, real Gold read); a redeploy is pending.

## What we are building

An assistant, not just a chatbot. It understands the customer, answers only with verified data, opens a dispute when the customer does not recognize a charge, confirms that the dispute exists, and hands the case to a person when needed. It works in **Spanish and Portuguese**.

The guiding principle: **AI understands; code executes and verifies.** The loop is the one the hackathon asks for: Understand → Decide → Act → Verify → Escalate. Policy, confirmations and the session live in code; the LLM never sees the customer's identifiers.

Two layers:

- **Data:** a Delta Lakehouse. S3 raw data → Bronze → Silver → Gold, with DuckDB locally and Azure Databricks in production, both running the same `sentinel_data` package.
- **Service:** one FastAPI process with the page, the orchestrator, the policy engine and four session-bound tools, and one API under `/api/v1`: `auth`, `transactions`, `chat`, `disputes` (two-step), `handoffs` (advisor) and `health`. Sessions, conversation state, disputes and handoff tickets live in SQLite, so a restart keeps them. Gold is read from the PII-free view in the pipeline's DuckDB file when `SENTINEL_GOLD_DUCKDB` or the repository's data path points at it, and from the labelled mock otherwise. Fraud and high-amount handoffs use synthetic thresholds per account country and currency that a bank replaces in configuration, and personal identifiers typed by the customer are masked before any model call. The service serves router_v2, a prompted LLM that only labels the intent, when a model is configured, and the keyword baseline otherwise and on any model failure, both behind one model port. Before the model is called, code refuses requests to reveal the prompt and records injection attempts; the shown charges are narrowed by what the customer said, and a "why?" is answered from the stored policy decision.
- **Human in the loop:** every handoff is filed as a ticket with the reason, a summary of the conversation, the verified facts and every action the system attempted; the advisor reads it in a read-only view of the same page.

The submission runs the same code with a few documented mocks (test session, SQLite instead of PostgreSQL, a demo advisor user, synthetic policy). See the [architecture](docs/architecture/README.md).

## Quickstart

Install and run the service (Python 3.12 or newer, from the repository root):

```bash
cd sentinel-ai-core
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app
```

Without a model configured the service serves the keyword baseline. To serve the measured router, copy `.env.example` to `.env`, fill in the `SENTINEL_LLM_*` values (see [`.env.example`](.env.example) and [the secrets guide](sentinel-ai-core/README.md)), load it with `set -a; source ../.env; set +a` and start `uvicorn` again; `GET /api/v1/health` shows the active model. To publish to Azure, see [`deploy/azure/README.md`](deploy/azure/README.md).

Open `http://localhost:8000/ui` and log in with a test customer (`CUST-0001`, `CUST-0002` or `CUST-0003`, password `Testpass-001`). These credentials are false and test-only.

To see the advisor side, start it with the demo roles enabled and log in as `ADV-0001` (password `Advisor-001`) after a customer has asked for a person twice:

```bash
cd sentinel-ai-core
SENTINEL_DEMO_AUTH=1 uvicorn app.main:app
```

State lives in `sentinel-ai-core/var/sentinel.db` (gitignored); delete it for a clean demo.

Watch the structured turn log while you chat (from the repository root):

```bash
tail -f sentinel-ai-core/var/turns.jsonl
```

Run the service tests:

```bash
cd sentinel-ai-core
python3 -m pytest tests/ -q
```

The data pipeline lives in [`sentinel-data-engine/`](sentinel-data-engine/README.md): sync the raw tables from the organizer bucket into `data/raw/` with the credentials in its `.env`, then build `data/gold_bank.duckdb` in one command (both gitignored; see its quickstart). Data sources are listed in the [inventory](docs/data_inventory.md).

## Requirements coverage

| Priority | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| P0 | 41 | 33 | 5 | 3 | 80% |
| P1 | 12 | 7 | 4 | 1 | 58% |
| P2 | 4 | 1 | 0 | 3 | 25% |
| **Total** | **57** | 41 | 9 | 7 | 72% |

| Status | Requirements |
|---|---|
| **Done** | Conversation and safety: REQ-0001 context · REQ-0002 clarify or abstain · REQ-0003 verified records only · REQ-0004 safe simulated tools · REQ-0005 verified actions · REQ-0006 answer, confirm or escalate (fraud and high amount per currency) · REQ-0007 permissions in code · REQ-0008 structured handoff · REQ-0033 policy decides · REQ-0040 request for a person, also with the confirm box open · REQ-0048 decision order. Demo: REQ-0009 normal case (real Gold locally) · REQ-0012 Spanish and Portuguese · REQ-0010 ambiguous · REQ-0011 human · REQ-0016 learned component vs baseline ([v7](evidence/evaluation-runs/2024Q4-eval-v7/summary.json)) · REQ-0017 valid labels, no leakage · REQ-0055 mandatory outcome metrics ([report](docs/build/metrics-report.md)) · REQ-0038 frontend · REQ-0039 freshness · REQ-0041 original currency · REQ-0042 candidates · REQ-0043 status check. Operations: REQ-0021 failure tests ([evidence](evidence/adversarial/20261002T222323Z/summary.json)) · REQ-0028 reproducible setup · REQ-0047 no personal data to the model (free text masked) · REQ-0025 observability · REQ-0026 retries and idempotency · REQ-0027 session, isolation, retention · REQ-0029 explanations from rules and logs · REQ-0032 documented mocks · REQ-0049 country as configuration. Data: REQ-0014 flow analysis ([selection](docs/build/flows/03-flow-selection.md)) · REQ-0018 incremental processing · REQ-0031 sources labeled by origin ([inventory](docs/data_inventory.md)) · REQ-0053 sizing ([capacity](docs/sizing_capacity.md)) · REQ-0054 no external data · Deployment: REQ-0035 [live link](docs/requirements/delivery.md#req-0035) |
| **In progress** | Data: REQ-0015 quality report generated in full (`quality-report`) · Analytics: REQ-0024 and REQ-0050 system outcomes per language and country and app monitoring, REQ-0057 ROI as a projection (`evaluation-final`) · ML: REQ-0019 experiment tracking · Delivery: REQ-0013 and REQ-0030 limits on the slides, REQ-0052 path to production with monitoring, REQ-0056 trade-offs in the presentation |
| **Pending** | Deliverables: REQ-0036 slides, REQ-0037 video, REQ-0051 language check · Optional: REQ-0044 local terms, REQ-0045 app-error context, REQ-0046 handoff routing, REQ-0023 LLM judge (not used) |

Status per requirement and per type: [requirements](docs/requirements/requirements.md#status-by-priority).

## Limitations

What the prototype does not do, stated up front (REQ-0013, REQ-0030; capacity in the [sizing](docs/sizing_capacity.md)):

- **Data:** synthetic and in Spanish only; accounts only in Mexico, Colombia and Argentina, and Mexican accounts only in USD. Real Gold runs locally: the app reads the PII-free view from the DuckDB file when it is present, excludes rows after the reference date, and `GET /api/v1/health` reports `duckdb` ([MT-09](team/chat-manual-tests.md)). The public link stays on the labeled mock. The case store is in memory on that local run, so a confirmation keeps `source=mock`.
- **Policy:** the dispute window is a declared demonstration policy (`synthetic: true`), not a bank's rule: one 90-day window serves Mexico, Colombia and Argentina. The sources read on 10/02 disagree — Argentina counts 30 days from receiving the statement, no fixed window was found for Colombia, and the Visa and Mastercard limits are bank-to-bank — and the engine cannot yet express a window start by country or a bank obligation such as provisional credit or a response time. Those are the production path, not built ([021](docs/build/decisions/021-dispute-policy-sources.md)). The "why?" answer says the rule is a demonstration policy and reads `window_days` from the country file, so the label disappears the day a bank sets `synthetic: false` with a verified value.
- **Languages:** the Portuguese (`pt-BR`) cases are model-written, with no native-speaker review, and variants are not strictly equivalent ([018](docs/build/decisions/018-evaluation-acceptance.md)). The three demo lines were back-translated by a second model. A Colombian check accepted the es-CO lines after the peso was named mexicano. Mexican and Argentine lines were checked by that model, not by a speaker. A 2% replay of the 2024Q4 transcripts, on the development side of the 70/30 time split, handed off all 280 times; the sample had 2 prefixes and no customer data was stored ([evidence](evidence/transcript-chats/20261002T144836Z/summary.json)). Those transcripts are templates, not customer language. Pix hands off. `extrato` and `fatura` stay charge words because the sealed set uses them inside charge inquiries.
- **Model:** the app serves router_v2 when `SENTINEL_LLM_*` are set, the configuration measured in [`2024Q4-eval-v7`](evidence/evaluation-runs/2024Q4-eval-v7/summary.json): 0.98 intent accuracy against 0.54 for the keyword baseline on the sealed set (n = 280), latency p50 1079 ms and p95 4475 ms for the router ([metrics report](docs/build/metrics-report.md)). When the model fails, that turn is answered by the baseline, which is the 0.54 level, and the turn log marks it. A greeting alone or small talk is classified as out of scope by the model (the sealed set has no such case); the chat answers it with an offer and hands off only on the third turn in a row. The router lowers risk, not effort: policy, confirmations and handoffs stay in code ([serving](sentinel-ai-core/app/ai/serving.py)).
- **State:** SQLite, one instance. On the public link it sits on the container's ephemeral disk, so a restart or scale-to-zero loses sessions and cases. Login-attempt and write-rate counters are per process.
- **Privacy:** free customer text is masked before the model, by pattern; personal data outside those patterns is not detected.
- **Narrowing:** the shown list now filters by merchant words, relative dates and repeated charges, and says when nothing matched (`charge.not_found`). A soft match does not open the confirm box. Approximate amounts and date phrases outside the listed set are not used. Offline on the MT-06 cases: right-charge-shown 20/24 before, 24/24 after; not-found-said 4/24 before, 24/24 after ([review](sentinel-ai-core/eval/review/narrowing.md)).
- **Safety evidence:** the adversarial set has 42 attacks with `0/42` unsafe outcomes. A3, A4b and D4 are `blocked_verified` (prompt extraction is refused in code, injection is recorded and not blocked, Gold reads time out under `SENTINEL_GOLD_TIMEOUT_S`, default 2 s). None remain in `no_defense_yet`. Three still pass only because the stand-in model is the keyword baseline ([run](evidence/adversarial/20261002T222323Z/summary.json)).
- **Resolution:** safe automated resolution is measured only as a simulation over the mock store. The resolution run [`2024Q4-resolution-v1`](evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) resolves 16 of 56 cases in 14 situations for both the baseline and router_v2, with 0 unsafe outcomes and 0 missed transfers, and a cost per resolution of USD 0.000561 for router_v2. It is not a field resolution rate: the set uses only the charges in the mock store, the pending status is not covered, and the paired difference between the versions is zero ([022](docs/build/decisions/022-resolution-acceptance.md)).
- **Deployment:** the live link serves router_v2 (checked 10/02) but runs an image built before PRs #49 and #50, so narrowing, the prompt-extraction refusal and the real Gold read are not live yet. State is on the container's ephemeral disk until the durable-storage change lands.

## Reading guide

1. **[The Challenge](docs/understand/overview.md):** what we must build, how we are judged and what we submit.
2. **[Architecture](docs/architecture/README.md):** the target system, the demo with its mocks, and the specification.
3. **[Flow selection](docs/build/flows/03-flow-selection.md):** why transaction disputes, backed by data and reproducible measurements.
4. **[Team plan](team/plan.md):** schedule, gantt, decisions made, working method and mocks.
5. **[Rationale](docs/rationale/README.md):** why each main choice was made, ready for the slides.

The [documentation index](docs/README.md) covers everything else.

## Repository map

| Path | What it holds |
|---|---|
| [`sentinel-data-engine/`](sentinel-data-engine/README.md) | Medallion pipeline (S3 → Bronze → Silver → Gold) over Delta Lake. DuckDB locally; Databricks mode implemented, not deployed. 13 LATAM Bank tables, ~19 M records. |
| [`sentinel-ai-core/`](sentinel-ai-core/) | Charge-inquiry loop and policy engine: FastAPI with one API under `/api/v1` (auth, chat, session-bound transactions, two-step disputes, advisor handoffs), policy engine, orchestrator and chat UI; sessions, conversation and cases in SQLite; a DuckDB Gold adapter over the pipeline's file that falls back to the labelled mock; the served router_v2 with a baseline fallback; the evaluation harness (`eval/`: development cases, the sealed held-out set and the multi-turn resolution set). Owners in [team/plan.md](team/plan.md#folders). |
| [`sentinel-login/`](sentinel-login/README.md) | Original demo page kept as a reference; not a backend and not served ([decision 009](docs/build/decisions/009-demo-ui-and-advisor-view.md)). |
| [`docs/architecture/`](docs/architecture/) | [System Architecture](docs/architecture/system-architecture.md), [Demo Architecture](docs/architecture/demo-architecture.md), [specification](docs/architecture/specification.md) |
| [`docs/understand/`](docs/understand/) | The challenge and the data: [The Challenge](docs/understand/overview.md), [dataset](docs/understand/dataset.md), [glossary](docs/understand/glossary/) |
| [`docs/requirements/`](docs/requirements/requirements.md) | What the system must do, traced to the hackathon material: an index with status and dependencies, and one file per type (frontend and backend, non-functional, data and ML, analytics, delivery) |
| [`docs/build/`](docs/build/) | How we build it: [areas](docs/build/areas/), [conversation](docs/build/conversation.md), [security](docs/build/security.md), [metrics](docs/build/metrics.md), [decisions](docs/build/decisions/), [delivery](docs/build/delivery.md) |
| [`evidence/`](evidence/) | Frozen, reproducible runs: the [flow measurements](evidence/flows/README.md), the [label evidence](evidence/evaluation/2024Q4-v1/summary.json), the [held-out measurement](evidence/evaluation-runs/2024Q4-eval-v7/summary.json), the [resolution run](evidence/evaluation-runs/2024Q4-resolution-v1/summary.json) and the [latest adversarial run](evidence/adversarial/20261002T222323Z/summary.json), cited by the documentation |
| [`scripts/`](scripts/) | Repository scripts, such as the generator of the flow measurements page |
| [`team/`](team/) | Plan, tasks and pending decisions |

## Team workflow

Planning lives in [`team/`](team/), apart from the project documentation:

- **[Pending decisions](team/pending-decisions.md):** what is still open and when it must be settled. Each teammate records a preference there.
- **[Tasks](team/tasks.md):** who does what, and by when.
- **[Plan](team/plan.md):** schedule, decisions made, working method and mocks.

## Rules that already apply

- **No secrets and no data in the repository.** The repository is public; credentials go in `.env` (excluded by `.gitignore`) and are shared by direct message.
- **Everything in English.** Code and documents are written in English; the assistant itself answers in Spanish and Portuguese.

## For agents

[`AGENTS.md`](AGENTS.md) explains the layout, the language rule and what must never be committed.
