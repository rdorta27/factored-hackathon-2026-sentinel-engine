# Documentation

This folder holds the challenge, the requirements, the design and the reasons for each choice. Team planning is in [`team/`](../team/). The measurement runs are in [`evidence/`](../evidence/README.md).

All documents are in English ([language](build/delivery.md#language)). The official hackathon material is not in the repository. The one exception is the data dictionary in [understand/reference/](understand/reference/).

## Reading order

Read these pages in this order. It takes about 20 minutes.

1. [The challenge](understand/overview.md)
2. [Architecture](architecture/README.md): the demo next to the target
3. [What is real and what is not](architecture/what-is-real.md)
4. [Requirements](requirements/requirements.md): the summary table and the P0 rows
5. [Rationale](rationale/README.md): why the system is built this way
6. [Evidence](../evidence/README.md): the runs that prove each claim

## Index by question

| Question | Document |
|---|---|
| What must we build, and when is it due? | [Overview](understand/overview.md) |
| How do the parts of the system fit together? | [Architecture](architecture/README.md), then [system](architecture/system-architecture.md) |
| What does the submission run? | [Demo architecture](architecture/demo-architecture.md) |
| Which parts are mocks, and which numbers are simulations? | [What is real](architecture/what-is-real.md) |
| Which run proves a claim? | [Evidence index](../evidence/README.md) |
| Why is it built this way? What do we say on each slide? | [Rationale](rationale/README.md) |
| Which requirement is done, and what proves it? | [Requirements](requirements/requirements.md) |
| What are the measured results? | [Metrics report](build/metrics-report.md) |
| What do we measure, and how do we split the data? | [Metrics](build/metrics.md), [ML](build/areas/ml.md#rigor) |
| Which flow did we choose, and what data supports it? | [Decision 003](build/decisions/003-disputes-flow.md), then [candidates](build/flows/01-flow-candidates.md), [measurements](build/flows/02-flow-measurements.md) and [selection](build/flows/03-flow-selection.md) |
| Why did we decide X? | [Decisions](build/decisions/) |
| What does the assistant say in each situation? | [Conversation](build/conversation.md) |
| What can the model see? How do we stop unauthorized access? | [Security](build/security.md), [what the model never receives](rationale/model-data-minimization.md) |
| How do we handle Portuguese? | [Conversation: languages](build/conversation.md#languages), [017](build/decisions/017-portuguese.md) |
| What does the deployment cost? What is the capacity? | [Cost](build/cost.md), [sizing and capacity](sizing_capacity.md) |
| Which data sources do we use, and where do they come from? | [Data inventory](data_inventory.md), [dataset](understand/dataset.md) |
| What do CSAT, PQR and held-out mean? | [Glossary](understand/glossary/) |
| What goes into the presentation and the video? | [Delivery](build/delivery.md) |
| Who does what, and when? | [Plan](../team/plan.md), [tasks](../team/tasks.md), [pending decisions](../team/pending-decisions.md) |

## Structure

| Folder or file | Purpose |
|---|---|
| [architecture/](architecture/) | The target, the demo and what is real |
| [understand/](understand/) | The challenge and the data in one read |
| [requirements/](requirements/) | What the system must do, with priority, area, evidence and status |
| [rationale/](rationale/) | Why each choice, with its evidence and the slide sentence |
| [build/](build/) | Areas, design rules, decisions, metrics and delivery |
| [reports/](reports/) | Generated reports for one requirement each (segments, country logs) |
| [data_inventory.md](data_inventory.md) | Data sources and their origin |
| [sizing_capacity.md](sizing_capacity.md) | Workload, capacity and latency targets |
| [`../evidence/`](../evidence/README.md) | Frozen measurement runs that the documents cite |
