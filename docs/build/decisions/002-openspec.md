---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 002 · Specifications with OpenSpec

**Date:** 2026-09-27
**Status:** Accepted
**Participants:** Team

## Context

We are three people with a deadline on 10/5, and we use AI assistants to write code. We need three things:

- A clear specification for each part before the implementation.
- Changes that a teammate can review.
- Specifications that also serve as documentation for the evaluation ("rationale and documentation" criterion).

## Options

1. **OpenSpec:** specification-driven development. Each change has a proposal with its motivation, its tasks and the requirements that it adds or changes. At the end, the specifications stay up to date.
2. **GitHub Issues only:** lighter, but the specifications go to many places.
3. **Free-form documents in `docs/`:** we have them already, but they do not guide the implementation step by step.

## Decision

OpenSpec, in the `openspec/` folder of the repository.

## Consequences

- **Relation with `docs/`:** `docs/` explains the challenge and the design rules. `openspec/` specifies what we build.
  - Each specification cites the requirements that it covers (for example, REQ-0008, JSON handoff).
  - The OpenSpec project context links to [system](../../architecture/system-architecture.md), [conversation](../conversation.md) and [security](../security.md). It does not copy them.
- **Language:** English (decision 18, closed 9/28), because the specifications are part of the public deliverable. *Updated 10/4:* written in ASD-STE100 ([AGENTS.md](../../../AGENTS.md)).
- **Workflow:** change proposal → pull-request review → implementation → archive of the change. A GitHub issue links to its proposal.
- OpenSpec is installed in the repository (`openspec/`). Each change proposal adds its specifications.
