# Sentinel AI Core

This package is the only submission server. `sentinel-login/` stays in the
repository as a reference and is not the server to start for the demo.

## Run

From this directory, with Python 3.12:

```
python3 -m uvicorn app.main:app --port 8000
```

The reference date is not the wall clock. The dataset ends on 2026-06-17, so
the real clock would put every charge outside the filing window. The process
reads `SENTINEL_REFERENCE_DATE` once at startup. Default: `2026-06-17`.

```
SENTINEL_REFERENCE_DATE=2026-06-17 python3 -m uvicorn app.main:app --port 8000
```

## Demo credentials (false, test-only)

| Login | Password | Country |
|---|---|---|
| `CUST-0001` | `Testpass-001` | MX |
| `CUST-0002` | `Testpass-001` | CO |
| `CUST-0003` | `Testpass-001` | AR |

Login is `POST /session/login` with `login` and `password`. Do not send
`customer_id` in the body.

## Model seam

The loop talks to `ModelPort.understand`. `create_app(model=...)` stores the
chosen model on `app.state.model` and defaults to the keyword baseline
(`DemoModel`), so the same loop runs with either implementation and no code
edit is needed to switch.

Set the `SENTINEL_LLM_*` variables (see the repo `.env.example`, names only,
no values) to run the prompted router; leave `SENTINEL_LLM_BASE_URL` empty to
stay on the baseline. The router picks a model per route (cheap frequent turns
vs. strong ambiguous or pt-BR turns) with a configured default fallback, and
reports `model`, `route`, `prompt_version`, tokens and cost on every
`understand` record. Tests replay committed fixtures under
`app/ai/fixtures/` and open no network connection.
