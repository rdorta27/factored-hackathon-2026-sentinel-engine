---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Cost

This page estimates the cost of the **minimal Azure deployment behind the public link of the demo** (REQ-0035). It is not a production cost estimate. The demo also runs locally at no cost.

**Status:** working assumption. It is the estimate of Natalia for the Azure production path. Nobody validated it against Azure pricing.

The submission runs on Azure Container Apps ([019](decisions/019-azure-container-apps.md)):

- The app stays inside the monthly free grant: 180,000 vCPU-seconds, 360,000 GiB-seconds and 2 million requests.
- The container registry costs about USD 0.08 a day.
- Both fit within the USD 200 trial credit.
- The only other metered spend is the LLM API. The provider caps it.

| Component | Service | Estimate (USD) |
|---|---|---|
| Compute | Azure Container Apps | 0–13 |
| LLM | Azure OpenAI, capped | 10–25 |
| Lakehouse | Azure Databricks | 10–20 |
| Secrets and storage | Key Vault, ADLS | 0–2 |
| **Total** | | **20–60** |

The total is the sum of the rows. The earlier figure of USD 20–58 did not match the rows. The upper bound is 60. Both fit within the USD 200 trial credit.

This page does not estimate production cost. REQ-0053 covers sizing and its limits. REQ-0057 covers cost per resolution.
