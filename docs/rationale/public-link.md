---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# What the public link runs

## Choice

The demo runs on Azure Container Apps in one container ([019](../build/decisions/019-azure-container-apps.md)):

- **Model:** `router_v2` (GLM 5.3 Flash, prompt v2), the configuration that `eval-v7` and the sealed `eval-v8` measured. The keyword baseline answers a turn when the model fails ([016](../build/decisions/016-router-models.md)). The service uses a separate Fireworks key with a spend cap. The key is a Container App secret (`SENTINEL_LLM_API_KEY`). The team revokes it after the evaluation.
- **Data:** the labelled Gold mock. `GET /api/v1/health` reports `gold_source: mock`. The dataset stays in the gitignored data folders.
- **State:** SQLite on an Azure Files share, mounted at `/mnt/sentinel`. One replica runs (`minReplicas 1`, `maxReplicas 1`) until the awards on 10/16. A restart keeps sessions, disputes and tickets.
- **Logs:** one JSON line per turn on standard output. Container Apps sends it to Log Analytics. A record holds no personal data.
- **Date:** a fixed reference date (2026-06-17), because the dataset ends in June 2026.

## Why

- **The brief accepts a minimal deployment** (REQ-0035, help channel 9/28).
- **No secrets and no data in the repository or the image** (AGENTS.md). Keys are host secrets only. Data stays local.
- **Test users map to the mock.** The link works without real Gold and shows no dataset row. The login has a lockout: after 10 failed logins, the link answers HTTP 429 for 15 minutes.
- **The window uses the reference date,** not the `CURRENT_DATE` columns of Gold. Static data does not fall outside the 90-day window.

## Evidence

| Check | Where | Result |
|---|---|---|
| The link serves `router_v2` on the mock | [REQ-0035](../requirements/delivery.md#req-0035), check of 2026-10-02 | `model` `accounts/fireworks/models/glm-5p3-flash`, `prompt_version` `v2`, `gold_source` `mock` |
| State survives a restart | REQ-0035, redeploy of 2026-10-03 from `main` (`9664d9d`) | a dispute and a handoff ticket were still present; health 200 |
| Turn records reach Log Analytics, counted by country | REQ-0035, same redeploy | a KQL count by country and outcome with no identifier |
| The final redeploy serves the frozen build | [`delivery`](../build/delivery.md#gate-g3-record), redeploy of 2026-10-05 | `GET /api/v1/health` returns `bundle_hash` `2efe5962f9a50d0b4fed8e7b91c10a4c7fd212d5229d74a2e58d1024ee96dfd2`, the hash of the sealed `2024Q4-eval-v8` run |
| Judge access | [`judge-access`](../../openspec/changes/archive/2026-10-05-judge-access/tasks.md) | The link has no passwordless entry. The documented fixture passwords do not work. The judges receive one shared set of credentials in the submission email |
| Deployment steps | [`deploy/azure/README.md`](../../deploy/azure/README.md) | reproducible script |

The live revision is from 2026-10-05. It serves the frozen build. Its `/health` `bundle_hash` equals the served hash of the sealed `2024Q4-eval-v8` run, so the measured behavior is the served behavior ([decision 018](../build/decisions/018-evaluation-acceptance.md)).

## Alternatives rejected

- **Ship a small DuckDB file.** This takes dataset rows out of the data folders and needs a login map for real customers.
- **Ephemeral disk.** A restart lost every session and case. The share fixes this for a few cents.

## In production

Real Gold through the Databricks reader, PostgreSQL, a key vault for secrets and more than one instance ([specification](../architecture/specification.md#path-to-production)).

## On the slide

"The public link runs the full flow on labelled mock data and the measured router, with the keyword baseline as a fallback. State survives a restart. The measured runs and their limits are in the repository."
