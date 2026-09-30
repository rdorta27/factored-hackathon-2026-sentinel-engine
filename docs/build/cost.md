# Cost

Estimated cost of the **minimal Azure deployment behind the demo's public link** (REQ-0035). It is not a production cost estimate. The demo can also run locally at no cost.

**Status:** working assumption ([decision 16](../../team/pending-decisions.md)), Natalia's estimate. Not validated against Azure pricing. The deployment itself is optional ([decision 13](../../team/pending-decisions.md)).

| Component | Service | Estimate (USD) |
|---|---|---|
| Compute | Azure Container Apps | 0–13 |
| LLM | Azure OpenAI, capped | 10–25 |
| Lakehouse | Azure Databricks | 10–20 |
| Secrets and storage | Key Vault, ADLS | 0–2 |
| **Total** | | **20–60** |

The total is the sum of the rows. The earlier figure of USD 20–58 did not match the rows; the upper bound is 60. Both fit within the USD 200 trial credit.

Production cost is not estimated. Sizing and its limits are REQ-0053; cost per resolution is REQ-0057.
