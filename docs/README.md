# Team documentation

The challenge, the requirements, and the design rules. Team planning lives in [`team/`](../team/). Everything is under construction: if something is unclear or missing, we adjust it.

We work in English. Everything we deliver — the repo README, the presentation, and the video script — as well as `docs/` and `team/` is written in English from the first draft; see [language](build/delivery.md#language).

The official hackathon material (problem statement, kickoff, and dataset summary) is not in the repository; each member keeps their own copy. The one exception is the data dictionary, kept as a column-level reference in [understand/reference/](understand/reference/).

## Reading order

If you are new, read in this order (about 20 minutes):

1. [The Challenge](understand/overview.md)
2. [Team plan](../team/plan.md): schedule and ways of working
3. [Architecture](architecture/README.md): demo next to the target
4. [Requirements](requirements/requirements.md): only the summary table and the P0s
5. Your area's document in [build/areas/](build/areas/)

## Index by question

| Question | Document |
|---|---|
| What must be built and when is it due? | [Overview](understand/overview.md) |
| How do the system pieces fit together? | [Architecture](architecture/README.md), then [system](architecture/system-architecture.md) |
| What does the submission actually run? | [Demo](architecture/demo-architecture.md) |
| Which mocks become real, and when? | [Plan](../team/plan.md#schedule) |
| What does the demo deployment cost? | [Cost](build/cost.md) |
| What do CSAT (Customer Satisfaction Score), PQR (Peticiones, Quejas y Reclamos — requests, complaints, and claims), held-out… mean? | [Glossary](understand/glossary/) |
| Which tables exist and what is each column for? | [Dataset](understand/dataset.md) |
| What is mandatory and which criterion still lacks evidence? | [Requirements](requirements/requirements.md) |
| Why is it built this way, and what do we say on each slide? | [Rationale](rationale/README.md) |
| What does the assistant say in each situation? | [Conversation](build/conversation.md) |
| What can the LLM see? How do we prevent unauthorized access? | [Security](build/security.md) |
| How do we handle Portuguese? | [Conversation: languages](build/conversation.md#languages) |
| What do we measure and how do we split the data? | [Metrics](build/metrics.md), [ML](build/areas/ml.md#rigor) |
| Which flow did we choose, and what data supports it? | [Decision 003](build/decisions/003-disputes-flow.md), then [candidate flows](build/flows/01-flow-candidates.md), [measurements](build/flows/02-flow-measurements.md) and [selection](build/flows/03-flow-selection.md) |
| Why did we decide X? | [Decisions](build/decisions/) |
| What goes into the presentation and the video? | [Delivery](build/delivery.md) |
| Who does what, when, and how do we work? | [Plan](../team/plan.md), [tasks](../team/tasks.md), [pending decisions](../team/pending-decisions.md) |

## Structure

| Folder or file | Purpose |
|---|---|
| [architecture/](architecture/) | Picture, target and demo |
| [understand/](understand/) | Understand the challenge and the data without reading everything |
| [requirements/](requirements/) | What the system must satisfy, with priority, area, evidence, and status |
| [build/](build/) | Areas, design rules, decisions, and delivery |
