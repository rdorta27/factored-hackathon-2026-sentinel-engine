# 014 · Data staleness rule off in the demo

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 27.

## Context

The staleness rule would stop answering from Gold and offer an advisor when Gold is older than a threshold. Freshness itself is a requirement: every answer states its as-of date and never claims anything newer (REQ-0039).

The dataset ends on 2026-06-17 and the demo's reference date is that same day, so Gold's age is always zero in the demo.

## Options

1. **Set a threshold now:** it could never fire in the demo or the evaluation, so it adds a rule nobody can see or test against real behavior.
2. **Leave it off in the demo and define it for production.**

## Decision

Option 2. The `staleness_days` entry stays null in the three country files, so the rule does not fire. The as-of date keeps being stated on every listing and confirmation, which is what the customer needs to know.

## Consequences

- No hidden behavior in the demo; freshness is covered by the stated as-of date (REQ-0039).
- Production: a per-country threshold in the same policy files, set by the bank from how often Gold refreshes, with a handoff when it is exceeded. Listed in the [path to production](../../architecture/specification.md#path-to-production).
