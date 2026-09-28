# Delivery

Monday 10/5 (time TBD). We work and deliver in **English**. The full list of deliverables is in the [overview](../understand/overview.md#deliverables-mon-105-time-to-be-confirmed).

## Language

Everything, working material included, is written in **English from the first draft**. There is no translation pass at the end: the README, the presentation, and the video script are drafted in English from the start. `docs/` and `team/` are translated. Registered as [REQ-0051](../requirements/requirements.md).

| Piece | Language | Status | Reviewed by | Frozen |
|---|---|---|---|---|
| Repo `README.md` (the delivery link) | English | Done | Rubén | Kept in English |
| GitHub repo title and description | English | Done | Rubén | Kept in English |
| Presentation (4 to 6 slides) | Born in English | Pending | | Fri 10/2 |
| Video script | Born in English | Pending | | Fri 10/2 |
| Demos: ES and PT cases | Spanish and Portuguese | — | — | What the system says |
| `docs/` and `team/` | English | — | — | Translated (decision 19 closed) |

We update it at each review, not at the end. Statuses: Pending, In progress, Done.

## Presentation

4 to 6 slides.

| # | Slide | Source |
|---|---|---|
| 1 | Problem and chosen flow, backed by data | [analysis](areas/analysis.md), [decisions](decisions/) |
| 2 | Architecture (core principle and layers) | [architecture](../understand/architecture.md), [decisions](decisions/) |
| 3 | Security and control: permissions, handoff, when NOT to act | [security](security.md), [conversation](conversation.md) |
| 4 | Results: baseline vs system (top metrics, by language) | [metrics](metrics.md) |
| 5 | Limitations and path to production | [requirements](../requirements/requirements.md) (REQ-0030, what is missing) |

- We show the 3 top metrics: safe resolution, unsafe outcomes, cost.
- Each figure with n and measurement type (offline, simulation, projection).
- We include failures and limitations; hiding them counts against us.

## Video pitch

Mandatory and short. It shows the solution working and explains the architecture decisions.

1. The problem, in one sentence and with one data point.
2. Demo of the **normal case** (ES).
3. Demo of the **ambiguous case** (PT).
4. Demo of the **human case**, showing the JSON handoff.
5. A prompt injection attempt that fails.
6. Key architecture decisions (from [decisions](decisions/)).
7. Top results and limitations.

## Pending

- [ ] Maximum video length (confirm with the organizers)
- [ ] Recording tool
