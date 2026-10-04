---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 001 · Platform: Microsoft Azure

**Date:** 2026-09-27
**Status:** Accepted
**Participants:** Team

## Context

The kickoff does not fix the tools. It suggests Azure, Snowflake, AWS and Databricks as options. We need three things:

- A place to deploy the tool (REQ-0035, deployed link).
- An LLM that respects the data limits: the LLM receives no personal data (PII) (REQ-0047), and we use approved data only (REQ-0031).
- A place to keep secrets.

## Options

1. **Azure:** one provider for the LLM, the deployment, the storage and the secrets. The kickoff suggests it.
2. **AWS:** equivalent services. The kickoff also suggests it.
3. **Separate free services** (Hugging Face Spaces, Render, free LLM APIs): no cost, but less control over the data and more parts to connect.

## Decision

Azure.

## Consequences

- Services to define (proposal, not yet confirmed):
  - **LLM:** Azure OpenAI (Azure AI Foundry). Make sure that it does not keep the data and does not use it for training. *Updated 9/28:* the team accepted a hybrid LLM with a router across models ([plan](../../../team/plan.md#decisions-made)). Decision 10 (Tue 9/29) chooses the model of each route and tells if Azure OpenAI is one of them.
  - **Deployment:** Azure Container Apps or App Service.
  - **Secrets:** Azure Key Vault or the environment variables of the service. Never in the repository.
  - **Data:** the location of the hackathon data (Azure storage or local).
- Open: who has the subscription or the credits. Set a **spend cap** and budget alerts from the first day.
- The public deployment needs usage limits against abuse ([security](../security.md#public-repository-and-deployment)).
- *Updated 9/29 ([System Architecture](../../architecture/system-architecture.md#stack-and-deployment)):* the Databricks pipeline is in the code (Asset Bundle, Bronze and Silver jobs), but it is not deployed. Gold on Databricks is for historical analytics. So the way the service reads charges at request time is not decided. The engine for the dispute records is not decided either: SQLite and PostgreSQL are candidates.
- The presentation must justify the choice: reproducibility, data control and deployment.
- *Updated 10/2:* the public link runs on Azure Container Apps ([019](019-azure-container-apps.md)). The router model runs on Fireworks AI ([016](016-router-models.md)).
