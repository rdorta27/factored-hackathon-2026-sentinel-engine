# Sentinel Engine

Factored AI & Data Hackathon 2026 · Submission: **Monday, October 5, 11:59 pm (UTC-5)**

A customer-service assistant for transaction disputes at a bank in Mexico, Colombia and Argentina. Work in progress: decisions are recorded as they are made, and open ones are marked as such.

## What we are building

An assistant, not just a chatbot. It understands the customer, answers only with verified data, opens a dispute when the customer does not recognize a charge, confirms that the dispute exists, and hands the case to a person when needed. It works in **Spanish and Portuguese**.

The guiding principle: **AI understands; code executes and verifies.**

## Requirements coverage

**0% covered (0 of 57 requirements Done)**: P0 0/41 · P1 0/12 · P2 0/4. All requirements are still Pending; see the [requirements](docs/requirements/requirements.md) for status.

## Start here (about 15 minutes)

1. **[The Challenge](docs/understand/overview.md):** what we must build, how we are judged and what we submit.
2. **[Architecture](docs/understand/architecture.md):** layers, components and mocks, decision priority and a case walkthrough, with diagrams.
3. **[Architecture and roadmap](docs/build/architecture-roadmap.md):** the 9/28 architecture proposal reconciled with the repository: personal data (PII) lifecycle, four-stage design, repository layout, timeline and costs.
4. **[Team plan](team/plan.md):** schedule, decisions made, working method and mocks.

The [documentation index](docs/README.md) covers everything else.

## Repository map

| Path | What it holds |
|---|---|
| [`docs/understand/`](docs/understand/) | The challenge, the system and the data: [The Challenge](docs/understand/overview.md), [architecture](docs/understand/architecture.md), [dataset](docs/understand/dataset.md), [glossary](docs/understand/glossary/) |
| [`docs/requirements/`](docs/requirements/requirements.md) | What the system must do, traced to the hackathon material, with priority, owner, evidence and status |
| [`docs/build/`](docs/build/) | How we build it: [areas](docs/build/areas/), [conversation](docs/build/conversation.md), [security](docs/build/security.md), [metrics](docs/build/metrics.md), [decisions](docs/build/decisions/), [delivery](docs/build/delivery.md), [roadmap](docs/build/architecture-roadmap.md) |
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
