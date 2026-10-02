# Cost

Estimated cost of the **minimal Azure deployment behind the demo's public link** (REQ-0035). It is not a production cost estimate. The demo can also run locally at no cost.

**Status:** working assumption, Natalia's estimate, for the Azure production path. Not validated against Azure pricing. The submission runs on Azure Container Apps: the app stays inside the monthly free grant (180,000 vCPU-seconds, 360,000 GiB-seconds, 2 million requests) and the container registry costs about USD 0.08/day, both inside the USD 200 trial credit ([019](decisions/019-azure-container-apps.md)); the only metered spend beyond hosting is the LLM API, capped at the provider.

| Component | Service | Estimate (USD) |
|---|---|---|
| Compute | Azure Container Apps | 0–13 |
| LLM | Azure OpenAI, capped | 10–25 |
| Lakehouse | Azure Databricks | 10–20 |
| Secrets and storage | Key Vault, ADLS | 0–2 |
| **Total** | | **20–60** |

The total is the sum of the rows. The earlier figure of USD 20–58 did not match the rows; the upper bound is 60. Both fit within the USD 200 trial credit.

Production cost is not estimated. Sizing and its limits are REQ-0053; cost per resolution is REQ-0057.
