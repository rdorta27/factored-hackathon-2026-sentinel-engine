# 019 · Public deployment on Azure Container Apps

**Date:** 2026-10-02
**Status:** Accepted
**Participants:** Rubén (owner); Felix deploys

Supersedes [012](012-public-deployment.md). The exception 012 wrote against [001](001-azure-platform.md) disappears: the submission now deploys on Azure itself.

## Context

REQ-0035 needs a link to the running tool before the Friday 10/2 code freeze. Decision 012 chose Hugging Face Spaces with the Docker SDK on 10/01, assuming a free CPU tier. The deploy on 10/02 proved the assumption stale: since July 2026, Hugging Face requires a paid plan for any Space that runs on compute (Docker included), the account quota for `cpu-basic` is `limit: 0`, and the Space stayed `PAUSED` with `Quota exceeded for flavor cpu-basic`. The official docs now read: *"CPU Basic has no hourly cost, but creating a new Space that runs on compute (Gradio or Docker) requires a paid plan. Static Spaces are free for everyone."* The Space `rdorta/sentinel-engine` was deleted the same day, and the HF deploy files left the repository.

The service itself did not change: one process (`python -m uvicorn app.main:app` from `sentinel-ai-core/`), SQLite on disk, the labeled Gold mock, secrets only as environment variables.

## Options

1. **Hugging Face Pro (about 9 USD/month):** puts the 012 setup one payment away; adds a billing account and a recurring cost for a demo that already has a cheaper home.
2. **Render free web service:** no card, 750 instance-hours per month; sleeps after 15 minutes, wakes in about a minute, and loses its local filesystem on every sleep (SQLite included).
3. **Azure Container Apps:** the platform decision 001 already chose; free monthly grant of 180,000 vCPU-seconds, 360,000 GiB-seconds and 2 million requests; scale-to-zero wakes in seconds; needs the Azure account created on 10/02 (trial credit of USD 200 for 30 days).
4. **AWS:** Fargate has no free tier, App Runner stopped accepting new customers on 4/30/2026, and every container path wants a card. Rejected.

## Decision

Azure Container Apps, one container, `minReplicas 1` and `maxReplicas 1` (amended 10/2: SQLite is per instance, so a second replica would not know the first one's sessions; amended again 10/2: one replica stays up until the awards on 10/16, so the first visit does not wait about 24 s for a cold start and the state is not lost to idle time, at about USD 1 to 2 per day, then it goes back to `minReplicas 0`), image stored in Azure Container Registry (Basic).

- **Aligned with [001](001-azure-platform.md):** the submission runs on the platform already chosen for production; the 012 exception exists no more.
- **Works when an evaluator opens it:** one replica stays up until the awards, so there is no cold start; the earlier scale-to-zero woke in about 24 s here, and the free grant no longer covers an always-on replica.
- **Cost inside published limits (REQ-0035):** ACR Basic is about 0.08 USD/day for the image, Container Apps stays inside the monthly free grant at this traffic, and both are covered by the trial credit. Hosting cannot run a few USD per month, with no usage surprises beyond the published free grant.
- **Same container, same code:** the Dockerfile from 012 moved to [deploy/azure](../../../deploy/azure/Dockerfile); [deploy.sh](../../../deploy/azure/deploy.sh) stages the build context, builds and pushes the image, and creates the app.
- **Secrets stay out of the image and the repo:** `SENTINEL_SESSION_SALT` is a Container App secret and `SENTINEL_SECURE_COOKIES=true` an app setting. The image bakes only non-secret defaults (mock Gold, SQLite, reference date, demo auth).
- **Ephemeral disk stays as 012 accepted it:** a scale-to-zero or restart may lose sessions and cases; logging in again is enough for a demo.

Configuration: `SENTINEL_DEMO_AUTH=1`, `SENTINEL_SECURE_COOKIES=true`, `SENTINEL_REFERENCE_DATE=2026-06-17`, a random `SENTINEL_SESSION_SALT`, Gold on the labeled mock (no dataset in the image).

## Consequences

- The link serves labeled mock data and router_v2 with a keyword-baseline fallback; the submission says so ([what the public link runs](../../rationale/public-link.md)).
- Until 10/16 the app does not scale to zero; after that it goes back to zero, and the first visit then waits for a cold start and finds an empty database, so the demo user logs in again. A redeploy recreates the app and empties the database as well.
- [Cost](../cost.md) records the Azure lines (registry plus free grant) instead of a free Hugging Face tier.
- Production stays on Azure, now one configuration away from the demo itself ([path to production](../../architecture/specification.md#path-to-production)).
- The HF attempt leaves no product trace: the Space is deleted and `deploy/hf-space/` is gone; only decision 012's history records it.
