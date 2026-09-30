# Delivery

Monday 10/5, 11:59 pm (UTC-5); the video lasts 3 minutes at most. We work and deliver in **English**. The full list of deliverables is in the [overview](../understand/overview.md#deliverables).

## Language

Everything, working material included, is written in **English from the first draft**. There is no translation pass at the end: the README, the presentation, and the video script are drafted in English from the start. `docs/` and `team/` are translated. Registered as [REQ-0051](../requirements/requirements.md).

| Piece | Language | Status | Reviewed by | Frozen |
|---|---|---|---|---|
| Repo `README.md` (the delivery link) | English | Done | Rubén | Kept in English |
| GitHub repo title and description | English | Done | Rubén | Kept in English |
| Presentation (4 to 6 slides) | Born in English | Pending | Rubén; group validates the outline Fri 10/2 | Outline Thu 10/1; reviewed Friday to Monday with the results; frozen Mon 10/5 |
| Video script | Born in English | Pending | Rubén | Script from Thu 10/1; frozen Mon 10/5 (internal deadline) |
| Demos: es-419 and pt-BR cases | Spanish and Portuguese | — | — | What the system says |
| `docs/` and `team/` | English | — | — | Translated (decision 19 closed) |

We update it at each review, not at the end. Statuses: Pending, In progress, Done.

## Presentation

4 to 6 slides.

| # | Slide | Source |
|---|---|---|
| 1 | Problem and chosen flow, backed by data | [flow selection](flows/03-flow-selection.md), [decisions](decisions/) |
| 2 | Architecture (core principle and layers) | [architecture](../architecture/README.md), [decisions](decisions/) |
| 3 | Security and control: permissions, handoff, when NOT to act | [security](security.md), [conversation](conversation.md) |
| 4 | Results: baseline vs system (top metrics, by language) | [metrics](metrics.md) |
| 5 | Limitations and path to production | [demo](../architecture/demo-architecture.md), [path to production](../architecture/specification.md#path-to-production) |

- We show the 3 top metrics: safe resolution, unsafe outcomes, cost.
- Each figure with n and measurement type (offline, simulation, projection).
- We include failures and limitations; hiding them counts against us.

## Video pitch

Mandatory, **3 minutes at most**. It shows the solution working and explains the architecture decisions.

1. The problem, in one sentence and with one data point.
2. Demo of the **normal case** (es-419).
3. Demo of the **ambiguous case** (pt-BR).
4. Demo of the **human case**, showing the JSON handoff.
5. A prompt injection attempt that fails.
6. Key architecture decisions (from [decisions](decisions/)).
7. Top results and limitations.

## Pending

- [x] Maximum video length: 3 minutes (confirmed 9/28)
- [ ] Recording tool
