# Sentinel Engine

Factored AI & Data Hackathon 2026 · Submission: **Monday, October 5, 11:59 pm (UTC-5)**

A customer-service assistant for transaction disputes at a bank in Mexico, Colombia and Argentina. Work in progress: decisions are recorded as they are made, and open ones are marked as such.

## What we are building

An assistant, not just a chatbot. It understands the customer, answers only with verified data, opens a dispute when the customer does not recognize a charge, confirms that the dispute exists, and hands the case to a person when needed. It works in **Spanish and Portuguese**.

The guiding principle: **AI understands; code executes and verifies.** The loop is the one the hackathon asks for: Understand → Decide → Act → Verify → Escalate. Policy, confirmations and the session live in code; the LLM never sees the customer's identifiers.

Two layers:

- **Data:** a Delta Lakehouse. S3 raw data → Bronze → Silver → Gold, with DuckDB locally and Azure Databricks in production, both running the same `sentinel_data` package.
- **Service:** one FastAPI process with the chat, the orchestrator, the policy engine and four session-bound tools. A prompted LLM classifies the dispute category and is measured against a keyword baseline.

The submission runs the same code with a few documented mocks (test session, in-memory dispute record, simulated advisor, synthetic policy). See the [architecture](docs/architecture/README.md).

## Requirements coverage

| Priority | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| P0 | 41 | 3 | 9 | 29 | 7% |
| P1 | 12 | 0 | 3 | 9 | 0% |
| P2 | 4 | 0 | 1 | 3 | 0% |
| **Total** | **57** | 3 | 13 | 41 | 5% |

| Status | Requirements |
|---|---|
| **Done** | REQ-0014 flow analysis ([selection](docs/build/flows/03-flow-selection.md)) · REQ-0033 policy decides, the LLM converses · REQ-0048 decision order ([specification](docs/architecture/specification.md#decision-priority)) |
| **In progress** | Designed, waiting for code: REQ-0004 safe tools · 0006 answer, confirm, escalate · 0008 JSON handoff · 0025 observability · 0029 explanations from sources · 0032 documented mocks · 0049 country as configuration · 0052 path to production · 0056 trade-offs · 0030 limitations. Data and ML: REQ-0015 pipeline · 0017 labels and splits · 0053 sizing |

Status per requirement: [requirements](docs/requirements/requirements.md#status-by-priority).

## Start here (about 15 minutes)

1. **[The Challenge](docs/understand/overview.md):** what we must build, how we are judged and what we submit.
2. **[Architecture](docs/architecture/README.md):** the target system, the demo with its mocks, and the specification.
3. **[Flow selection](docs/build/flows/03-flow-selection.md):** why transaction disputes, backed by data and reproducible measurements.
4. **[Team plan](team/plan.md):** schedule, gantt, decisions made, working method and mocks.

The [documentation index](docs/README.md) covers everything else.

## Repository map

| Path | What it holds |
|---|---|
| [`sentinel-data-engine/`](sentinel-data-engine/README.md) | Medallion pipeline (S3 → Bronze → Silver → Gold) over Delta Lake. DuckDB locally; Databricks mode implemented, not deployed. 13 LATAM Bank tables, ~19 M records. |
| `sentinel-ai-core/` | Not created yet. One FastAPI process: chat, orchestrator, policy, tools, observability and the evaluation runner. Owners in [team/plan.md](team/plan.md#folders). |
| [`docs/architecture/`](docs/architecture/) | [System Architecture](docs/architecture/system-architecture.md), [Demo Architecture](docs/architecture/demo-architecture.md), [specification](docs/architecture/specification.md) |
| [`docs/understand/`](docs/understand/) | The challenge and the data: [The Challenge](docs/understand/overview.md), [dataset](docs/understand/dataset.md), [glossary](docs/understand/glossary/) |
| [`docs/requirements/`](docs/requirements/requirements.md) | What the system must do, traced to the hackathon material, with priority, owner, evidence and status |
| [`docs/build/`](docs/build/) | How we build it: [areas](docs/build/areas/), [conversation](docs/build/conversation.md), [security](docs/build/security.md), [metrics](docs/build/metrics.md), [decisions](docs/build/decisions/), [delivery](docs/build/delivery.md) |
| [`evidence/`](evidence/) | Frozen, reproducible runs of the flow measurements (and later the evaluation), cited by the documentation |
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
