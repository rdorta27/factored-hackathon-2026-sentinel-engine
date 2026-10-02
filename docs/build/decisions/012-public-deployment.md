# 012 · Public deployment on Hugging Face Spaces

**Date:** 2026-10-01
**Status:** Superseded by 019
**Participants:** Rubén (owner); Felix deploys

Closes pending decisions 13 (deployment target for the submission) and 16 (who provides the subscription). An exception to [decision 001](001-azure-platform.md) for the submission only: Azure stays the production target.

## Context

The submission needs a link to the working tool (REQ-0035), and "first and foremost the solution should work" is the first evaluation criterion. A minimal deployment is enough and cloud is not mandatory (help channel, 9/28). Azure has no subscription or credits assigned yet, and code freezes on Friday 10/2.

The service is one long-running process (`uvicorn app.main:app` from `sentinel-ai-core/`) with SQLite on disk, the labeled Gold mock, and secrets only as environment variables. It does not depend on any cloud service.

## Options

1. **Azure Container Apps:** consistent with decision 001, but blocked on a subscription, and the setup competes with Friday's code freeze.
2. **Hugging Face Spaces (Docker):** free CPU tier that runs the container unchanged, secrets in the Space settings, public HTTPS URL, sleeps only after about 48 hours without visits.
3. **Render (web service):** free and simple, but the free tier sleeps after about 15 minutes, so an evaluator arriving cold waits about a minute.
4. **Fly.io or Railway:** good fit with volumes for SQLite, but no real free tier for new accounts; needs a card.
5. **Vercel:** built for frontends and serverless functions; it does not keep a uvicorn process or a SQLite file. Rejected.

Free-tier terms change often; they were checked on 2026-10-01 and must be checked again before deploying.

## Decision

Hugging Face Spaces with the Docker SDK, one container, one instance.

- **It works when an evaluator opens it.** The 48-hour idle window covers the evaluation period with one visit a day from the team, while Render's 15 minutes would leave most visits starting cold.
- **No cost and no billing account.** Nothing to cap on the host. The only metered spend is the LLM API once decision 10 lands, capped at the provider.
- **Same container, same code.** No code change: a `Dockerfile` that runs `uvicorn app.main:app` on the port the Space exposes. What runs on the link is what the tests and frozen runs measure.
- **Secrets stay out of the image and the repo:** `SENTINEL_SESSION_SALT`, and later `SENTINEL_LLM_API_KEY`, are Space secrets.
- **Ephemeral disk fits what was already accepted:** a restart may lose sessions and cases; logging in again is enough, and one instance avoids sharing SQLite.
- **Familiar to an AI jury:** Spaces is a common place to show AI demos.

Configuration: `SENTINEL_DEMO_AUTH=1` (advisor view), `SENTINEL_SECURE_COOKIES=true`, `SENTINEL_REFERENCE_DATE=2026-06-17`, a random `SENTINEL_SESSION_SALT`, Gold on the labeled mock (no dataset in the image).

## Consequences

- The link serves labeled mock data and, until decision 10, the keyword baseline; the submission says so ([what the public link runs](../../rationale/public-link.md)).
- First visit after 48 idle hours starts cold; the team opens the link daily during evaluation, and the submission notes the first load may be slow.
- A public Space shows its files; the repository is already public and the image holds no secrets or data.
- Production stays on Azure: Container Apps with autoscaling, Key Vault for secrets, PostgreSQL instead of SQLite ([path to production](../../architecture/specification.md#path-to-production)).
- Pending: the `Dockerfile` and the Space itself (Felix, REQ-0035).
