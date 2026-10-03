# Design

## Context

On `main` after PR #53: `deploy/azure/deploy.sh` mounts an Azure Files share, sets the `DELETE` journal and standard-output records, pins one replica, and falls back to a random salt when `.env` has none. `.github/workflows/tests.yml` runs both suites and the gitleaks scan and has `runs=()`. A restart check and a per-country count in Log Analytics are recorded under REQ-0035. See proposal.md for motivation.

## Decisions

1. **Fail on a missing salt:** a generated salt dies with the deploy and breaks correlation.
2. **Replay list grows with merges:** each change that freezes a replayable run adds it to the list in its own PR; this change seeds it with `2024Q4-resolution-v1` and tries `2024Q4-eval-v7`.
3. **Final redeploy once,** after the work shown in the video merges; a short script fetches health and the locale file and runs the demo cases; queries live in `deploy/azure/queries.kql`.

## Risks / Trade-offs

- **Log ingestion delay:** queries run a few minutes after the traffic.
- **The deploy recreates the app:** done before recording, never during.
