# Sentinel Engine

Felix, Natalia and Rubén · Factored AI & Data Hackathon 2026 · Submission: **Monday, October 5** (time to be confirmed)

Our starting point. Almost everything here is a proposal and gets adjusted as we go.

## What we are building

A **customer service assistant for a bank** operating in Mexico, Colombia and Argentina. The idea is not just another chatbot: it should understand the customer, answer with verified data, perform safe actions, confirm that they happened, and hand the case over to a person when needed. It has to work in **Spanish and Portuguese**.

## Start here (about 15 minutes)

1. **[The challenge in one page](docs/understand/overview.md):** what has to be built, how we are judged and what we submit.
2. **[Architecture](docs/understand/architecture.md):** layers, decision priority and the guiding principle (AI understands; code executes and verifies), with diagrams.
3. **[Architecture and roadmap](docs/build/architecture-roadmap.md):** PII lifecycle, 4-layer design, repository layout, timeline and costs, with pending decisions marked.
4. **[Team plan](team/plan.md):** tentative schedule and how we propose to work.

The [documentation index](docs/README.md) helps you find the rest of the topics.

## Repository map

| Path | What it holds |
|---|---|
| [`docs/understand/`](docs/understand/) | The challenge, the system and the data: [overview](docs/understand/overview.md), [architecture](docs/understand/architecture.md), [dataset](docs/understand/dataset.md), [glossary](docs/understand/glossary/) |
| [`docs/requirements/`](docs/requirements/requirements.md) | Requirements with priority, owner, evidence and status |
| [`docs/build/`](docs/build/) | How we build it: [areas](docs/build/areas/), [conversation](docs/build/conversation.md), [security](docs/build/security.md), [metrics](docs/build/metrics.md), [decisions](docs/build/decisions/), [delivery](docs/build/delivery.md) and the [roadmap](docs/build/architecture-roadmap.md) |
| [`team/`](team/) | Plan, tasks and pending decisions |

## Team workflow

Planning lives in [`team/`](team/), separate from the project documentation:

- **[Pending decisions](team/pending-decisions.md):** on Monday 28/9 we decide the flow, the owners per area, the working method and the stack. Everyone records their preference there.
- **[Tasks](team/tasks.md):** who does what, and by when.
- **[Plan](team/plan.md):** team, schedule, mock strategy, working method and decisions taken.

## Hackathon rules that already apply

- **No secrets and no data in the repository.** The repository is delivered public; credentials go in `.env` (excluded by `.gitignore`) and are shared by direct message.
- **Submission in English.** Everything in this repository is written in English, including working documents; the system itself answers in Spanish and Portuguese.

## For agents

[`AGENTS.md`](AGENTS.md) explains the layout, the language rule and what must never be committed.
