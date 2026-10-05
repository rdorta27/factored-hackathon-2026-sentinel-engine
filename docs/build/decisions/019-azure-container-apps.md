---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 019 · Public deployment on Azure Container Apps

**Date:** 2026-10-02
**Status:** Accepted
**Participants:** Rubén (owner); Felix deploys

Supersedes [012](012-public-deployment.md). The exception of 012 to [001](001-azure-platform.md) disappears: the submission now deploys on Azure itself.

## Context

REQ-0035 needs a link to the running tool before the code freeze on Friday 10/2. Decision 012 chose Hugging Face Spaces with the Docker SDK on 10/01, on the assumption of a free CPU tier. The deploy on 10/02 showed that the assumption was old:

- Since July 2026, Hugging Face requires a paid plan for each Space that runs on compute, Docker included.
- The account quota for `cpu-basic` is `limit: 0`.
- The Space stayed `PAUSED` with `Quota exceeded for flavor cpu-basic`.

The official docs now say: *"CPU Basic has no hourly cost, but creating a new Space that runs on compute (Gradio or Docker) requires a paid plan. Static Spaces are free for everyone."* We deleted the Space `rdorta/sentinel-engine` the same day, and the HF deploy files left the repository.

The service did not change: one process (`python -m uvicorn app.main:app` from `sentinel-ai-core/`), SQLite on disk, the labelled Gold mock, and secrets only as environment variables.

## Options

1. **Hugging Face Pro (about 9 USD per month):** the setup of 012 after one payment. It adds a billing account and a recurring cost for a demo that already has a cheaper place.
2. **Render free web service:** no card, 750 instance-hours per month. It sleeps after 15 minutes, wakes in about one minute, and loses its local filesystem (SQLite included) at each sleep.
3. **Azure Container Apps:** the platform of decision 001. A free monthly grant of 180,000 vCPU-seconds, 360,000 GiB-seconds and 2 million requests. Scale-to-zero wakes in seconds. It needs the Azure account created on 10/02 (trial credit of USD 200 for 30 days).
4. **AWS:** Fargate has no free tier. App Runner stopped new customers on 4/30/2026. Every container path wants a card. Rejected.

## Decision

Azure Container Apps, one container, `minReplicas 1` and `maxReplicas 1`. The image is in Azure Container Registry (Basic).

- *Amended 10/2:* SQLite is per instance, so a second replica does not know the sessions of the first.
- *Amended again 10/2:* one replica stays up until the awards on 10/16. The first visit does not wait about 24 s for a cold start, and idle time does not lose the state. This costs about USD 1 to 2 per day. After the awards, the app goes back to `minReplicas 0`.

The reasons:

- **Aligned with [001](001-azure-platform.md):** the submission runs on the platform that we chose for production. The exception of 012 does not exist any more.
- **It works when an evaluator opens it:** one replica stays up until the awards, so there is no cold start. Scale-to-zero woke in about 24 s here, and the free grant does not cover an always-on replica.
- **Cost inside published limits (REQ-0035):** ACR Basic is about 0.08 USD per day for the image. Container Apps stays inside the monthly free grant at this traffic. The trial credit covers both. Hosting costs a few USD per month at most.
- **Same container, same code:** the Dockerfile of 012 moved to [deploy/azure](../../../deploy/azure/Dockerfile). [deploy.sh](../../../deploy/azure/deploy.sh) prepares the build context, builds and pushes the image, and creates the app.
- **Secrets stay out of the image and the repository:** `SENTINEL_SESSION_SALT` is a Container App secret. `SENTINEL_SECURE_COOKIES=true` is an app setting. The image contains only non-secret defaults (mock Gold, SQLite, reference date, demo auth).
- **Ephemeral disk, as 012 accepted it:** a scale-to-zero or a restart can lose sessions and cases. A new login is sufficient for a demo. *Updated 10/3:* the deploy now mounts an Azure Files share, and a restart keeps the state (see the consequences).

Configuration: `SENTINEL_DEMO_AUTH=1` (the advisor role), `SENTINEL_DEMO_PERSONAS=0` (no one-click entry on the link), `SENTINEL_USERS_PATH=/mnt/sentinel/users.json` (the judge credentials, hashes only), `SENTINEL_SECURE_COOKIES=true`, `SENTINEL_REFERENCE_DATE=2026-06-17`, a random `SENTINEL_SESSION_SALT`, and Gold on the labelled mock (no dataset in the image).

## Consequences

- The link serves labelled mock data and `router_v2` with a keyword-baseline fallback. The submission says so ([what the public link runs](../../rationale/public-link.md)).
- Until 10/16 the app does not scale to zero. After that date it goes back to zero, and the first visit waits for a cold start.
- *Updated 10/3:* the deploy mounts an Azure Files share at `/mnt/sentinel` for the SQLite file and the turn log. A dispute and a handoff ticket survived `az containerapp revision restart` ([REQ-0035](../../requirements/delivery.md#req-0035), [deploy notes](../../../deploy/azure/README.md)). A redeploy recreates the app, but the share keeps the file.
- [Cost](../cost.md) records the Azure lines (registry and free grant) instead of a free Hugging Face tier.
- Production stays on Azure, one configuration step away from the demo ([path to production](../../architecture/specification.md#path-to-production)).
- The HF attempt leaves no product trace: the Space is deleted and `deploy/hf-space/` is gone. Only the history of decision 012 records it.
- *Updated 10/5:* the link has no one-click entry and no documented password. The judges receive one shared set of credentials in the submission email. The users file holds salted hashes only and lives on the share ([`judge-access`](../../../openspec/changes/judge-access/tasks.md), [deploy notes](../../../deploy/azure/README.md)).
