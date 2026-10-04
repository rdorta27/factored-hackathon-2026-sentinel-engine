---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# What the public link runs

## Choice

The demo runs on Azure Container Apps in one container ([019](../build/decisions/019-azure-container-apps.md)):

- **Model:** `router_v2` (GLM 5.3 Flash, prompt v2), the configuration measured in `eval-v7`. The keyword baseline answers a turn when the model fails ([016](../build/decisions/016-router-models.md)). The service uses a separate Fireworks key with a spend cap. The key is a Container App secret (`SENTINEL_LLM_API_KEY`). The team revokes it after the evaluation.
- **Data:** the labelled Gold mock. `GET /api/v1/health` reports `gold_source: mock`. The dataset stays in the gitignored data folders.
- **State:** SQLite on an Azure Files share, mounted at `/mnt/sentinel`. One replica runs (`minReplicas 1`, `maxReplicas 1`) until the awards on 10/16. A restart keeps sessions, disputes and tickets.
- **Logs:** one JSON line per turn on standard output. Container Apps sends it to Log Analytics. A record holds no personal data.
- **Date:** a fixed reference date (2026-06-17), because the dataset ends in June 2026.

## Why

- **The brief accepts a minimal deployment** (REQ-0035, help channel 9/28).
- **No secrets and no data in the repository or the image** (AGENTS.md). Keys are host secrets only. Data stays local.
- **Test users map to the mock.** The link works without real Gold and shows no dataset row.
- **The window uses the reference date,** not the `CURRENT_DATE` columns of Gold. Static data does not fall outside the 90-day window.

## Evidence

| Check | Where | Result |
|---|---|---|
| The link serves `router_v2` on the mock | [REQ-0035](../requirements/delivery.md#req-0035), check of 2026-10-02 | `model` `accounts/fireworks/models/glm-5p3-flash`, `prompt_version` `v2`, `gold_source` `mock` |
| State survives a restart | REQ-0035, redeploy of 2026-10-03 from `main` (`9664d9d`) | a dispute and a handoff ticket were still present; health 200 |
| Turn records reach Log Analytics, counted by country | REQ-0035, same redeploy | a KQL count by country and outcome with no identifier |
| Deployment steps | [`deploy/azure/README.md`](../../deploy/azure/README.md) | reproducible script |

The live revision is from 2026-10-03. It does not have PRs #55 and #56 yet. The final redeploy is planned before the video (`live-ops`).

## Alternatives rejected

- **Ship a small DuckDB file.** This takes dataset rows out of the data folders and needs a login map for real customers.
- **Ephemeral disk.** A restart lost every session and case. The share fixes this for a few cents.

## In production

Real Gold through the Databricks reader, PostgreSQL, a key vault for secrets and more than one instance ([specification](../architecture/specification.md#path-to-production)).

## On the slide

"The public link runs the full flow on labelled mock data and the measured router, with the keyword baseline as a fallback. State survives a restart. The measured runs and their limits are in the repository."
