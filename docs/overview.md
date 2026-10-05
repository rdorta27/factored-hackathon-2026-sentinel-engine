# The Challenge

**Purpose:** understand the hackathon without reading the PDFs. **Related:** [system](architecture/system-architecture.md), [dataset](data/dataset.md), [requirements](requirements/requirements.md), [glossary](glossary/).

> "Build something that works, prove that it works, and know when it should not act. And show us what it would take to make it real."

## Objective

A **customer-support assistant for a bank** operating in Mexico, Colombia, and Argentina. Not a chatbot: a **system** that understands the customer, queries verified data, executes safe actions, verifies that they happened, and hands the case to a person when appropriate.

- **A single flow**, one of: account or payment inquiries, cards, transaction disputes, or credit information and eligibility. Adding more flows does not score points on its own: depth and engineering judgment count. Ours is transaction disputes ([decision 003](build/decisions/003-disputes-flow.md)).
- It must work in **Spanish and Portuguese**. The data is only in Spanish.
- **End-to-end working first**; then we optimize.

## Demo cases

| Case | What the assistant does |
|---|---|
| Normal | Resolves it alone, following bank policies |
| Ambiguous or unsupported | Asks for what is missing or says it cannot help |
| Requires a person | Escalates with a structured summary for the advisor |

## Golden rules

This is the summary; the detail lives in [system](architecture/system-architecture.md) and [conversation](build/conversation.md).

1. **AI understands; code executes and verifies.** Permissions live in code, not in the prompt.
2. **Only verified facts.** If the data is missing or not current, we say so.
3. **Autonomy depends on risk.** Actions with consequences require confirmation.
4. **Honesty.** We report failures, limitations, and what is missing for production.

## Evaluation

| Criterion | What they look at |
|---|---|
| Rationale and documentation | Why we chose the flow, written decisions, limitations |
| AI Engineering | Backend, frontend, and deployment |
| Data Analytics | Data quality and insights |
| Data Engineering | Extraction and transformation pipeline |
| Machine Learning | Selection, evaluation against a baseline, and model tracking |

Main metrics: **safe automated resolution**, **unsafe outcomes**, and **cost**. Detail in [metrics](build/metrics.md).

## Deliverables

Deadline: **Monday 10/5, 11:59 pm (UTC-5)**, confirmed by the organizers on 9/28.

The challenge is a 10-day sprint: it starts 9/25 and submissions close 10/5.

We send to hackathon.admin@factored.ai:

1. Public repository `factored-hackathon-2026-[team]`
2. Link to the deployed tool
3. 4-to-6-slide presentation
4. Video of **3 minutes at most**: demo and architecture decisions

"Submit your tool no matter what": we deliver on time, with limitations declared.

## Known risks

- **Portuguese without data:** evaluators will most likely test in Brazilian Portuguese. See [languages](build/conversation.md#languages).
- **Data with intentional issues:** duplicates, nulls, late arrivals, changing schema. See [dataset](data/dataset.md).
- **Nobody on the team comes from contact centers:** the [glossary](glossary/) explains the business acronyms.

## Official material

*Problem statement* · *Kickoff* · *Dataset summary* · *Data dictionary*
