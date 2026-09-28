# 001 · Platform: Microsoft Azure

**Date:** 2026-09-27
**Status:** Accepted
**Participants:** Team

## Context

The kickoff leaves tooling open and suggests Azure, Snowflake, AWS, and Databricks as optional. We need somewhere to deploy the tool (REQ-0035, deployed link), an LLM that meets the data limits (REQ-0047, the LLM receives no personal data (PII); REQ-0031, approved data), and somewhere to store secrets.

## Options

1. **Azure:** a single provider for LLM, deployment, storage, and secrets. Suggested at the kickoff.
2. **AWS:** equivalent in services; also suggested.
3. **Loose free services** (Hugging Face Spaces, Render, free LLM APIs): no cost, but less control over data and more pieces to integrate.

## Decision

Azure.

## Consequences

- Services to define (proposal, pending confirmation):
  - **LLM:** Azure OpenAI (Azure AI Foundry). Verify that it neither retains data nor uses it for training. *Updated 9/28:* the team accepted a hybrid LLM with a router across models ([plan](../../../team/plan.md#decisions-made)); which model serves each route, and whether Azure OpenAI is one of them, is pending (decision 10, Tue 9/29).
  - **Deployment:** Azure Container Apps or App Service.
  - **Secrets:** Azure Key Vault or the service's environment variables; never in the repository.
  - **Data:** wherever the hackathon data lands (Azure storage or local).
- Pending: who holds the subscription or credits, and setting a **spending cap** and budget alerts from day one.
- The public deployment needs usage limits to prevent abuse (see [security](../security.md#public-repository-and-deployment)).
- The presentation must justify the choice: reproducibility, data control, and deployment.
