---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 012 · Public deployment on Hugging Face Spaces

**Date:** 2026-10-01
**Status:** Superseded by 019
**Participants:** Rubén (owner); Felix deploys

Closes pending decisions 13 (deployment target for the submission) and 16 (who provides the subscription). An exception to [decision 001](001-azure-platform.md) for the submission only: Azure stays the production target.

> *Superseded on 10/2:* Hugging Face removed its free Docker tier. The public link runs on Azure Container Apps ([019](019-azure-container-apps.md)). The text below is the record of the decision at that date.

## Context

The submission needs a link to the working tool (REQ-0035). The first evaluation criterion is "first and foremost the solution should work". A minimal deployment is sufficient, and cloud is not mandatory (help channel, 9/28). Azure has no subscription or credits yet. The code freezes on Friday 10/2.

The service is one long-running process (`uvicorn app.main:app` from `sentinel-ai-core/`). It has SQLite on disk, the labelled Gold mock, and secrets only as environment variables. It does not depend on a cloud service.

## Options

1. **Azure Container Apps:** consistent with decision 001. It waits for a subscription, and the setup competes with the Friday freeze.
2. **Hugging Face Spaces (Docker):** a free CPU tier that runs the container with no change. Secrets in the Space settings. A public HTTPS URL. It sleeps only after about 48 hours without visits.
3. **Render (web service):** free and simple. The free tier sleeps after about 15 minutes, so an evaluator who arrives cold waits about one minute.
4. **Fly.io or Railway:** a good fit, with volumes for SQLite. No real free tier for new accounts. It needs a card.
5. **Vercel:** made for frontends and serverless functions. It does not keep a uvicorn process or a SQLite file. Rejected.

The terms of free tiers change often. We checked them on 2026-10-01. Check them again before a deploy.

## Decision

Hugging Face Spaces with the Docker SDK, one container, one instance.

- **It works when an evaluator opens it.** The 48-hour idle window covers the evaluation period with one visit a day from the team. With the 15 minutes of Render, most visits start cold.
- **No cost and no billing account.** Nothing to cap on the host. The only metered spend is the LLM API after decision 10, capped at the provider.
- **Same container, same code.** No code change: a `Dockerfile` that runs `uvicorn app.main:app` on the port of the Space. The link runs what the tests and the frozen runs measure.
- **Secrets stay out of the image and the repository.** `SENTINEL_SESSION_SALT`, and later `SENTINEL_LLM_API_KEY`, are Space secrets.
- **An ephemeral disk fits what we accepted.** A restart can lose sessions and cases. A new login is sufficient. One instance does not share SQLite.
- **Known to an AI jury.** Spaces is a common place for AI demos.

Configuration: `SENTINEL_DEMO_AUTH=1` (advisor view), `SENTINEL_SECURE_COOKIES=true`, `SENTINEL_REFERENCE_DATE=2026-06-17`, a random `SENTINEL_SESSION_SALT`, and Gold on the labelled mock (no dataset in the image).

## Consequences

- The link serves labelled mock data and, until decision 10, the keyword baseline. The submission says so ([what the public link runs](../../rationale/public-link.md)).
- The first visit after 48 idle hours starts cold. The team opens the link each day during the evaluation. The submission says that the first load can be slow.
- A public Space shows its files. The repository is already public, and the image has no secrets and no data.
- Production stays on Azure: Container Apps with autoscaling, Key Vault for secrets, and PostgreSQL instead of SQLite ([path to production](../../architecture/specification.md#path-to-production)).
- Open at that date: the `Dockerfile` and the Space itself (Felix, REQ-0035).
