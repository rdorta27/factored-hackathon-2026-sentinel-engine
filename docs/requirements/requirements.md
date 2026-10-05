---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Requirements

This page lists what the system must do to meet the hackathon brief. Each requirement has an ID (`REQ-####`). The rest of the documentation cites it. The table is also the traceability matrix. Each requirement links to:

- the official document that it comes from,
- the evaluation criterion that it serves,
- the area that owns it,
- the evidence that proves it,
- its status.

**Purpose:** set the priority of the work, find the evaluation criteria that still have no evidence, and see what blocks what ([dependencies](#dependencies)). **Related:** [The Challenge](../overview.md), [dataset](../data/dataset.md), [glossary](../glossary/), [evidence index](../../evidence/README.md), [what is real](../architecture/what-is-real.md).

## Hackathon material

The requirements come from four official documents and from the clarifications in the help channel. The documents are not in the repository, except the data dictionary, kept as a column reference in [data/reference/](../data/reference/). Each teammate keeps a copy. We cite them by section or page.

| Document | Cited as | What it defines | Requirements that cite it |
|---|---|---|---|
| Problem statement (*Factored AI & Data Hackathon 2026*) | Problem statement: *section* | Scope, what the solution must demonstrate, data and execution boundaries, submission | 38 |
| Kickoff deck (*Datathon 2026 kickoff*) | Kickoff p. *N* | Evaluation criteria, workflows, multilingual support, headline metrics | 36 |
| Dataset summary (*LATAM Bank*) | Dataset summary | Tables, volumes and the intentional quality problems (duplicates, nulls, late arrivals, schema changes) | 6 |
| Data dictionary (*LATAM Bank*) | Dictionary | Columns, partitions and relationships between tables | 1 |
| Answers in the hackathon help channel | Help channel (*date*) | Clarifications: what counts as a learned component, cloud deployment, sizing, external data, deadline | 6 |

A requirement with no official source has the mark **Own**: a design decision of the team, with a link to its explanation. 8 requirements have only this source. Others combine it with an official source. The dataset documents shape the data requirements through [dataset](../data/dataset.md). We cite them when a row depends on a declared property of the data.

## Classification

| Column | Values |
|---|---|
| **Type** | **Frontend and backend** = what the customer and the advisor see, and the service behind it · **Non-functional** = how: security, reliability, operations · **Data and ML** = pipeline, sources, learned component · **Analytics** = analysis and metrics · **Delivery** = what the evaluators receive. A mixed requirement is in its main type. The *Area* column shows the others |
| **Priority** | **P0** = mandatory for the submission on Mon 10/5, 11:59 pm (UTC-5) · **P1** = scores points · **P2** = only if time remains |
| **Flow** | "All", or the flow it depends on (transaction disputes, see [decision 003](../build/decisions/003-disputes-flow.md)) |
| **Criterion** | Kickoff evaluation criterion: Rationale, AI Engineering, Data Engineering, Data Analytics, Machine Learning |
| **Area** | The areas that work on it. The first one owns it, and the others help: [ai](../build/areas/ai.md) · [ml](../build/areas/ml.md) · [data](../build/areas/data.md) · [analysis](../build/areas/analysis.md) |
| **Status** | Pending, In progress, Done. Update it when the task that covers it closes |
| **Source** | Official document and section or page (see [hackathon material](#hackathon-material)), or **Own** |
| **Depends on** | Requirements that must be met first (see [dependencies](#dependencies)) |

Each type has a summary table here, and its own file with one card per requirement: description, source, dependencies and evidence. **Evidence** tells what proves the requirement today (*Proven by*) and what is still necessary (*Missing*).

## Summary by priority

| Priority | Count | What it includes |
|---|---|---|
| P0 | 41 | The 3 demo cases, es-419 and pt-BR, verification, permissions in code, handoff, learned component vs baseline, outcome metrics, explicit trade-offs, pipeline with contracts and real incremental processing, failure tests, deliverables, delivery language, path to production, sizing |
| P1 | 12 | Tracking, business outcomes and ROI, observability, retries, breakdown by language and country, fine-grained conversation rules |
| P2 | 4 | Country as configuration, app-error context, handoff routing, LLM judge |

## Status by priority

Counted from the *Status* column of the tables below. Update it when a status changes.

| Priority | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| P0 | 41 | 34 | 5 | 2 | 83% |
| P1 | 12 | 11 | 0 | 1 | 92% |
| P2 | 4 | 1 | 0 | 3 | 25% |
| **Total** | **57** | 46 | 5 | 6 | 81% |

## Status by type

| Type | Total | Done | In progress | Pending | Done % |
|---|---|---|---|---|---|
| [Frontend and backend](frontend-backend.md) | 19 | 16 | 0 | 3 | 84% |
| [Non-functional](non-functional.md) | 13 | 12 | 1 | 0 | 92% |
| [Data and ML](data-ml.md) | 10 | 9 | 0 | 1 | 90% |
| [Analytics](analytics.md) | 7 | 7 | 0 | 0 | 100% |
| [Delivery](delivery.md) | 8 | 2 | 4 | 2 | 25% |
| **Total** | **57** | 46 | 5 | 6 | 81% |

## Frontend and backend

What the customer and the advisor see, and the service behind it: conversation, verified answers, tools, policy and handoff. Cards: [frontend-backend.md](frontend-backend.md).

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0001](frontend-backend.md#req-0001) | Keep conversation context | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0002](frontend-backend.md#req-0002) | Clarify or abstain | P0 | ai | [REQ-0001](frontend-backend.md#req-0001), [REQ-0003](frontend-backend.md#req-0003) | Done |
| [REQ-0003](frontend-backend.md#req-0003) | Answer only from verified records | P0 | ai | [REQ-0015](data-ml.md#req-0015), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0004](frontend-backend.md#req-0004) | Use tools safely, simulated actions only | P0 | ai | [REQ-0005](non-functional.md#req-0005), [REQ-0007](non-functional.md#req-0007), [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0006](frontend-backend.md#req-0006) | Decide answer, confirm or escalate | P0 | ai | [REQ-0007](non-functional.md#req-0007), [REQ-0033](frontend-backend.md#req-0033) | Done |
| [REQ-0008](frontend-backend.md#req-0008) | Structured handoff package | P0 | ai | [REQ-0003](frontend-backend.md#req-0003), [REQ-0029](non-functional.md#req-0029), [REQ-0047](non-functional.md#req-0047) | Done |
| [REQ-0009](frontend-backend.md#req-0009) | Demo: normal case | P0 | ai | [REQ-0003](frontend-backend.md#req-0003), [REQ-0004](frontend-backend.md#req-0004), [REQ-0006](frontend-backend.md#req-0006), [REQ-0012](frontend-backend.md#req-0012) | Done |
| [REQ-0010](frontend-backend.md#req-0010) | Demo: ambiguous or unsupported case | P0 | ai | [REQ-0002](frontend-backend.md#req-0002) | Done |
| [REQ-0011](frontend-backend.md#req-0011) | Demo: case requiring a human | P0 | ai | [REQ-0008](frontend-backend.md#req-0008), [REQ-0040](frontend-backend.md#req-0040) | Done |
| [REQ-0012](frontend-backend.md#req-0012) | Works in Spanish and Portuguese | P0 | ai, ml | [REQ-0001](frontend-backend.md#req-0001) | Done |
| [REQ-0033](frontend-backend.md#req-0033) | Policy decides, the LLM converses | P0 | ai, ml | [REQ-0048](non-functional.md#req-0048) | Done |
| [REQ-0038](frontend-backend.md#req-0038) | Simple frontend | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0040](frontend-backend.md#req-0040) | Request for a person | P0 | ai | [REQ-0006](frontend-backend.md#req-0006) | Done |
| [REQ-0041](frontend-backend.md#req-0041) | Original currency, customer's language | P0 | ai | [REQ-0003](frontend-backend.md#req-0003) | Done |
| [REQ-0042](frontend-backend.md#req-0042) | Minimum-effort dispute opening | P1 | ai | [REQ-0003](frontend-backend.md#req-0003), [REQ-0038](frontend-backend.md#req-0038) | Done |
| [REQ-0043](frontend-backend.md#req-0043) | Check charge status first | P1 | ai | [REQ-0003](frontend-backend.md#req-0003), [REQ-0015](data-ml.md#req-0015) | Done |
| [REQ-0044](frontend-backend.md#req-0044) | Neutral Spanish with local terms | P1 | ai | [REQ-0012](frontend-backend.md#req-0012) | Pending |
| [REQ-0045](frontend-backend.md#req-0045) | App-error context | P2 | ai | [REQ-0001](frontend-backend.md#req-0001) | Pending |
| [REQ-0046](frontend-backend.md#req-0046) | Handoff routing (simulated) | P2 | ai | [REQ-0008](frontend-backend.md#req-0008), [REQ-0012](frontend-backend.md#req-0012) | Pending |

## Non-functional

How the system behaves: security, privacy, reliability, observability and reproducibility. Cards: [non-functional.md](non-functional.md).

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0005](non-functional.md#req-0005) | Report only verified actions | P0 | ai | [REQ-0032](non-functional.md#req-0032) | Done |
| [REQ-0007](non-functional.md#req-0007) | Permissions and policy in code | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0021](non-functional.md#req-0021) | Failure tests | P0 | ml, ai | [REQ-0007](non-functional.md#req-0007), [REQ-0012](frontend-backend.md#req-0012), [REQ-0026](non-functional.md#req-0026), [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0025](non-functional.md#req-0025) | Observability | P1 | ai | — | Done |
| [REQ-0026](non-functional.md#req-0026) | Bounded retries and safe fallback | P1 | ai | [REQ-0005](non-functional.md#req-0005) | Done |
| [REQ-0027](non-functional.md#req-0027) | Authentication, isolation and retention | P0 | ai, data | — | Done |
| [REQ-0028](non-functional.md#req-0028) | Reproducible setup | P0 | all | [REQ-0015](data-ml.md#req-0015), [REQ-0019](data-ml.md#req-0019) | Done |
| [REQ-0029](non-functional.md#req-0029) | Explanations from sources and rules | P1 | ai | [REQ-0025](non-functional.md#req-0025) | Done |
| [REQ-0032](non-functional.md#req-0032) | Documented mock tools | P1 | ai | — | Done |
| [REQ-0047](non-functional.md#req-0047) | No personal data to the LLM | P0 | ai | [REQ-0027](non-functional.md#req-0027) | Done |
| [REQ-0048](non-functional.md#req-0048) | Decision order | P0 | ai, ml | [REQ-0016](data-ml.md#req-0016) | Done |
| [REQ-0049](non-functional.md#req-0049) | Country as configuration | P2 | ai | — | Done |
| [REQ-0056](non-functional.md#req-0056) | Explicit trade-offs | P0 | all | [REQ-0016](data-ml.md#req-0016), [REQ-0055](analytics.md#req-0055) | In progress |

## Data and ML

Data preparation, sources and freshness, and the learned component with its labels, splits and tracking. Cards: [data-ml.md](data-ml.md).

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0015](data-ml.md#req-0015) | Repeatable pipeline with contracts | P0 | data | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0016](data-ml.md#req-0016) | Learned component vs baseline | P0 | ml | [REQ-0017](data-ml.md#req-0017), [REQ-0020](data-ml.md#req-0020) | Done |
| [REQ-0017](data-ml.md#req-0017) | Valid labels, no leakage | P0 | ml | [REQ-0015](data-ml.md#req-0015) | Done |
| [REQ-0018](data-ml.md#req-0018) | Real incremental processing | P0 | data | [REQ-0015](data-ml.md#req-0015) | Done |
| [REQ-0019](data-ml.md#req-0019) | Experiment tracking | P1 | ml | [REQ-0016](data-ml.md#req-0016) | Done |
| [REQ-0020](data-ml.md#req-0020) | Same held-out for baseline and system | P0 | ml | [REQ-0017](data-ml.md#req-0017) | Done |
| [REQ-0023](data-ml.md#req-0023) | Validated LLM judge, if used | P2 | ml | [REQ-0016](data-ml.md#req-0016) | Pending |
| [REQ-0031](data-ml.md#req-0031) | Approved data, labeled by origin | P0 | data | — | Done |
| [REQ-0039](data-ml.md#req-0039) | Declare data freshness | P0 | ai, data | [REQ-0015](data-ml.md#req-0015) | Done |
| [REQ-0054](data-ml.md#req-0054) | Justified external data | P1 | data, ml | [REQ-0031](data-ml.md#req-0031) | Done |

## Analytics

The analysis that justifies the flow, and the metrics that prove that the system works. Cards: [analytics.md](analytics.md).

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0014](analytics.md#req-0014) | Data-backed problem | P0 | analysis | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0022](analytics.md#req-0022) | Metrics with n, mix and variability | P0 | analysis | [REQ-0020](data-ml.md#req-0020), [REQ-0055](analytics.md#req-0055) | Done |
| [REQ-0024](analytics.md#req-0024) | Breakdown by language, country and segment | P1 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0022](analytics.md#req-0022) | Done |
| [REQ-0050](analytics.md#req-0050) | Monitoring by country | P1 | analysis | [REQ-0024](analytics.md#req-0024), [REQ-0025](non-functional.md#req-0025) | Done |
| [REQ-0053](analytics.md#req-0053) | Sizing and its limits | P0 | analysis | [REQ-0014](analytics.md#req-0014) | Done |
| [REQ-0055](analytics.md#req-0055) | Mandatory outcome metrics | P0 | analysis, ml | [REQ-0020](data-ml.md#req-0020), [REQ-0025](non-functional.md#req-0025) | Done |
| [REQ-0057](analytics.md#req-0057) | Business outcomes and ROI | P1 | analysis | [REQ-0055](analytics.md#req-0055) | Done |

## Delivery

What the evaluators receive: repository, deployed link, slides, video, limitations and the path to production. Cards: [delivery.md](delivery.md).

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0013](delivery.md#req-0013) | Report data and language limits | P0 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0024](analytics.md#req-0024) | In progress |
| [REQ-0030](delivery.md#req-0030) | Declare what is missing | P0 | all | [REQ-0013](delivery.md#req-0013), [REQ-0053](analytics.md#req-0053) | In progress |
| [REQ-0034](delivery.md#req-0034) | Clean public repository | P0 | all | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0035](delivery.md#req-0035) | Deployed tool link | P0 | ai | [REQ-0027](non-functional.md#req-0027), [REQ-0034](delivery.md#req-0034) | Done |
| [REQ-0036](delivery.md#req-0036) | Presentation, 4 to 6 slides | P0 | all | [REQ-0055](analytics.md#req-0055), [REQ-0056](non-functional.md#req-0056) | Pending |
| [REQ-0037](delivery.md#req-0037) | Video pitch | P0 | all | [REQ-0009](frontend-backend.md#req-0009), [REQ-0010](frontend-backend.md#req-0010), [REQ-0011](frontend-backend.md#req-0011), [REQ-0035](delivery.md#req-0035) | Pending |
| [REQ-0051](delivery.md#req-0051) | Everything in English | P0 | all | [REQ-0036](delivery.md#req-0036), [REQ-0037](delivery.md#req-0037) | In progress |
| [REQ-0052](delivery.md#req-0052) | Path to production | P0 | ai, all | [REQ-0025](non-functional.md#req-0025), [REQ-0050](analytics.md#req-0050) | In progress |

## Dependencies

A requirement depends on another when we cannot meet it, or cannot produce its evidence, until the other one is met. Each requirement lists its direct dependencies in its table row, and with the reason in its card. Update them when you add a requirement or when its evidence changes.

Chains that still block P0 work (status on 2026-10-05):

- **Data and learned component:** closed. REQ-0015, REQ-0016, REQ-0017, REQ-0019 and REQ-0020 are done.
- **Deployment and video:** REQ-0035 (Done) → REQ-0037 (Pending) → REQ-0051 (In progress). The final redeploy comes before the video.
- **Slides:** REQ-0055 (Done) → REQ-0056 (In progress) → REQ-0036 (Pending) → REQ-0051.
- **Limitations:** REQ-0024 (Done) → REQ-0013 (In progress) → REQ-0030 (In progress). The limits must go on the slides, and the README needs a roadmap section.
- **Path to production:** REQ-0052 (In progress) needs alerts by country (REQ-0050).

We write the statuses in these chains by hand. Update them when a requirement changes status.

## Future work (not requirements)

- More Latin American countries. REQ-0049 (country as configuration) makes this easier. Each new country needs data, rules, a currency and tests.
- Streaming: only if a flow needs freshness in seconds.

## Open questions

None. The reference labels are model-written simulation cases and the frozen label universe of the data (`evidence/evaluation/2024Q4-v1/summary.json`). The human-required cases are the `requires_handoff` cases in `sentinel-ai-core/eval/cases/`.
