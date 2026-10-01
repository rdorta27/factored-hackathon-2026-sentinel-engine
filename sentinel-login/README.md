# Sentinel Login (reference demo UI, not a backend)

This folder keeps the **original demo page** of the Sentinel Engine prototype:
`app/ui/static/` (HTML, JavaScript, styles) and its locale files in
`app/ui/i18n/`. It is **not a backend and it is not served**.

The submission runs one process, `sentinel-ai-core/`, which serves the API
under `/api/v1` and the page at `/ui/`: the customer chat and, for the demo
advisor role, the view of escalated tickets. See
[decision 009](../docs/build/decisions/009-demo-ui-and-advisor-view.md).

What moved and where:

| Was here | Now |
|---|---|
| Login, sessions, roles, lockout, audit | `sentinel-ai-core/app/session/` (`/api/v1/auth/*`) |
| Chat, grounding, case store | `sentinel-ai-core/app/orchestrator/`, `app/routers/demo_chat.py`, `app/state/` |
| Disputes, eligibility policy | `sentinel-ai-core/app/policy/`, `app/routers/disputes.py` |
| Gold mock store | `sentinel-ai-core/app/tools/gold.py` (+ DuckDB adapter) |
| Advisor queue | `GET /api/v1/handoffs` (read-only) and the advisor view of the page |
| Admin metrics and audit | Not migrated (decision 009); the structured log covers observability |
| Demo users | `sentinel-ai-core/app/session/fixtures/users.json` |

Demo credentials are false and test-only; they are documented in
`sentinel-ai-core/README.md`. The advisor user exists only with
`SENTINEL_DEMO_AUTH=1`.

Once nobody needs this page as a reference, the folder can be removed.
