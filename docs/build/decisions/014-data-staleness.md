---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# 014 · Data staleness rule off in the demo

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 27.

## Context

The staleness rule stops answers from Gold and offers an advisor when Gold is older than a threshold. Freshness itself is a requirement: every answer states its as-of date and never claims a newer date (REQ-0039).

The dataset ends on 2026-06-17. The reference date of the demo is the same day. So the age of Gold is always zero in the demo.

## Options

1. **Set a threshold now:** it can never fire in the demo or in the evaluation. It adds a rule that nobody can see or test against real behavior.
2. **Keep it off in the demo and define it for production.**

## Decision

Option 2. The `staleness_days` entry stays null in the three country files, so the rule does not fire. Every list and every confirmation still states the as-of date. This is what the customer needs to know.

## Consequences

- No hidden behavior in the demo. The stated as-of date covers freshness (REQ-0039).
- Production: a threshold per country in the same policy files. The bank sets it from the refresh rate of Gold, with a handoff when Gold is older. The [path to production](../../architecture/specification.md#path-to-production) lists it.
