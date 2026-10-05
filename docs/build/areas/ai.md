---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# AI Engineering

**Evaluation criterion:** backend, frontend and deployment.

**Owners:** Rubén (AI and architecture). Felix (backend, frontend and deployment).

**Requirements:** those in the `ai` area in the [requirements table](../../requirements/requirements.md).

**Related:** [system](../../architecture/system-architecture.md), [demo](../../architecture/demo-architecture.md), [conversation](../conversation.md) (what the assistant says) and [security](../security.md).

## Scope

- **Orchestrator:** the loop Understand, Decide, Act, Verify and Escalate. The decision order is policy, then predictor, then LLM.
- **Tools** (mock): each tool has a documented contract. The session customer filters its data. It returns the data and the date of the last update.
- **Policies in code:** what the system answers alone, what needs a confirmation and when it makes a handoff.
- **Handoff:** a JSON document with a schema that code can validate.
- **Frontend:** a simple chat. No dashboard.
- **Deployment:** a public link, usage limits and a spending cap.
- **Observability:** execution traces and logs. Each record has the country and the language, for [country monitoring](analysis.md#country-monitoring).

## Technical rules

- Retries have a limit. Actions are idempotent: a repeated action does not duplicate its effect.
- Country is configuration, not code. Configuration files hold the currency, documents, terms, regulator and deadlines of each country. Today the countries are MX, CO and AR.

## Handoff

### Schema (draft)

```json
{
  "solicitud": "",
  "idioma": "es | pt",
  "pais_cuenta": "MX | CO | AR",
  "hechos_verificados": [],
  "acciones_realizadas": [],
  "evidencia": [],
  "preguntas_abiertas": [],
  "motivo_escalamiento": ""
}
```

### Simulated routing

The router uses `service_agents` to pick an active advisor. The advisor speaks the language of the customer and has the specialty of the flow. See [dataset](../../data/dataset.md#dictionary-supporting-dimensions).

## Evidence for evaluation

- [x] Demo of the three cases (normal, ambiguous and human) in es-419 and pt-BR ([REQ-0009](../../requirements/frontend-backend.md#req-0009), [REQ-0010](../../requirements/frontend-backend.md#req-0010), [REQ-0011](../../requirements/frontend-backend.md#req-0011))
- [x] Working deployed link ([REQ-0035](../../requirements/delivery.md#req-0035)). The live revision is from 10/5. See [delivery](../delivery.md).
- [x] Auditable execution logs ([REQ-0025](../../requirements/non-functional.md#req-0025))
- [x] Reproducible installation instructions ([REQ-0028](../../requirements/non-functional.md#req-0028))

## Pending decisions

No decision is open. These two are closed:

- Hybrid LLM models: decision [016](../decisions/016-router-models.md) sets the router and its models. Decisions [005](../decisions/005-backend.md) and [006](../decisions/006-frontend.md) set the backend and the frontend.
- Deployment service on Azure: Container Apps, decision [019](../decisions/019-azure-container-apps.md).
