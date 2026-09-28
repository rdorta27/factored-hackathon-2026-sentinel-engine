# 002 · Specifications with OpenSpec

**Date:** 2026-09-27
**Status:** Accepted
**Participants:** Team

## Context

We are 3 people with a deadline of 10/5 and AI assistants for coding. We need every piece to have a clear specification before implementation, changes to be reviewable, and specifications to serve as documentation for the evaluation ("rationale and documentation" criterion).

## Options

1. **OpenSpec:** specification-driven development. Each change is proposed with its motivation, tasks, and the requirements it adds or modifies; when finished, the specifications stay up to date.
2. **GitHub Issues only:** lighter, but specifications end up scattered.
3. **Free-form documents in `docs/`:** we already have them, but they are not designed to guide implementation step by step.

## Decision

OpenSpec, in the repository's `openspec/` folder.

## Consequences

- **Relationship with `docs/`:** `docs/` explains the challenge and the design rules; `openspec/` specifies what gets built.
  - Each specification cites the requirements it covers (e.g., REQ-0008, JSON handoff).
  - The OpenSpec project context links to [architecture](../../understand/architecture.md), [conversation](../conversation.md), and [security](../security.md), instead of copying them.
- **Language:** to be defined. The specifications are part of the public deliverable, so writing them in English is preferable.
- **Workflow:** change proposal → pull-request review → implementation → change archival. GitHub issues link to their proposal.
- Pending: install OpenSpec and initialize the folder after choosing the flow (Monday 9/28).
