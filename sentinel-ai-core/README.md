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
