# What the public link runs

## Choice

The deployed demo runs on Hugging Face Spaces, one container ([012](../build/decisions/012-public-deployment.md)), with:

- **Model:** the keyword baseline. The router models are measured offline ([016](../build/decisions/016-router-models.md)); if the link serves them, it uses a separate, disposable Fireworks key with a spending cap, stored only as a Space secret (`SENTINEL_LLM_API_KEY`) and revoked after evaluation.
- **Data:** the labeled Gold mock (`gold_source: mock` on `/api/v1/health`). The dataset never leaves the gitignored `data/` folder.
- **State:** SQLite on the host, one instance. A restart may lose sessions and cases; for a demo, logging in again is enough.
- **Date:** a configurable reference date (2026-06-17), because the dataset ends in June 2026.

## Why

- **The brief accepts a minimal deployment** and does not require cloud (REQ-0035, help channel 9/28).
- **No secrets or data in the repo or image** (AGENTS.md rules): keys only as host secrets, data only local.
- **Test users map to the mock,** so the link works without real Gold and without exposing rows.
- **The window is recomputed from the reference date,** not from Gold's `CURRENT_DATE` columns, so static data does not fall outside the 90-day window.

## Alternatives rejected

- **Ship a small DuckDB:** takes dataset rows out of `data/` and needs a real-customer login map.
- **Persistent volume as a requirement:** worth it if the host gives one for free, not a blocker.

## In production

Real Gold through the DuckDB or Databricks reader, Postgres, a key vault for secrets, several instances.

## On the slide

"The public link runs the full flow on labeled mock data and the keyword baseline; the measured runs and their limits are in the repository."
