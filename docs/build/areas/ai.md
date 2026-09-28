# AI Engineering

**Evaluation criterion:** backend, frontend, and deployment. **Owners:** Rubén (AI and architecture); Felix (backend, frontend, and deployment).

**Requirements:** those in the `ai` area in the [requirements table](../../requirements/requirements.md).

**Related:** [architecture](../../understand/architecture.md), [conversation](../conversation.md) (what the assistant says), [security](../security.md).

## Scope

- **Orchestrator:** the understand, decide, act, verify, and escalate loop, with decision order policy > predictor > LLM.
- **Tools** (mock) with documented contracts, filtered by the session's customer, returning the data and its last-updated date.
- **Policies in code:** what it answers on its own, what requires confirmation, and when to escalate.
- **Handoff** in JSON with a validatable schema.
- **Simple frontend** (chat). No dashboard.
- **Deployment** with a public link, usage limits, and a spending cap.
- **Observability:** execution traces and logs, with country and language on every record (for [country monitoring](analysis.md#country-monitoring)).

## Technical rules

- Bounded retries; idempotent actions (repeating them does not duplicate them).
- Country is configuration, not code: currency, documents, terms, regulator, and deadlines for each country live in configuration files. Today MX, CO, and AR.

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

With `service_agents` we pick an active advisor who speaks the customer's language and has the specialty of the flow. See [dataset](../../understand/dataset.md#dictionary-supporting-dimensions).

## Evidence for evaluation

- [ ] Demo of the 3 cases (normal, ambiguous, human) in es-419 and pt-BR
- [ ] Working deployed link
- [ ] Auditable execution logs
- [ ] Reproducible installation instructions

## Pending decisions

- Hybrid LLM models (the router is already decided; backend and frontend are [005](../decisions/005-backend.md) and [006](../decisions/006-frontend.md))
- Deployment service on Azure
