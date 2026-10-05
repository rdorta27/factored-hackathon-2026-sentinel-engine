---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Order

The change runs before `pitch-site` closes. The slides and the site cite its numbers. It depends on `eval-v8` (task 1.4 reports and task 3.1 rehearsal). Its live runs move to `post-freeze`.

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| Gap analysis | Replay only. No live call | The recordings of `resolution-v2` already hold both answers. The analysis costs nothing |
| New resolution cases | Only if the analysis shows the set cannot separate the two systems | Extra cases change the sealed claim. We add them under a new hash. We do not edit a sealed set |
| Latency | One live run on the frozen build, with a spend cap | A replay time is not an end-to-end time. The brief asks for p50 and p95 |
| Label | Simulation, live model call, mock store | The data and the store stay synthetic. Only the model call is live |
| Effective sample size | Report bases next to cases | 405 cases come from 70 bases. The base is the unit of independence |
| Human check | 20 labels, one reviewer, agreement reported | It checks label quality. It is not an LLM judge, so REQ-0023 stays not applicable |
| Negative results | One rationale page, linked from the rationale index | A rejected component with a fixed rule shows rigor (decision 025) |

## Risks

| Risk | Control |
|---|---|
| The analysis shows the router adds nothing to resolution | State it. The gain is in intent and in safe handoff. Do not edit the claim |
| A live run costs more than planned | The runner stops at the spend cap |
| A change after the freeze | Not allowed. A fix reopens gate G3 |
