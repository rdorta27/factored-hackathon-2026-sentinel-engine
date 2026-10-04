---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# 005 · Backend: Python, FastAPI (LangGraph deferred)

**Date:** 2026-09-28
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 9.

## Context

The skeleton for Tuesday needs an HTTP API and an orchestrator. The team uses Python. .NET is out. The loop is Understand → Decide → Act → Verify → Escalate. Policy, the session and idempotency are in code, not in the prompt (REQ-0007).

## Options

1. **Python + FastAPI, loop in plain Python.** The smallest option for Tuesday. We must rewrite the confirmation, retry and handoff path when the ambiguous case arrives.
2. **Python + FastAPI, LangGraph in the same process.** The graph is only the loop. Policy, the session and idempotency stay in code. One process to deploy.
3. **A separate LangGraph service, or a Node API.** A second process before the deploy on Thursday, with no gain for four tools.

## Decision

Python with FastAPI.

- Decided now: the language and the framework.
- Deferred: LangGraph or plain Python for the loop. The skeleton starts with the smallest loop that meets the contracts.
- In both cases, policy, the authenticated session and idempotency stay in code, and no orchestrator ever sees `customer_id`.

## Consequences

- The orchestrator can replace a mock tool with a real store without a change to its protocol.
- LangGraph stays an option for the loop, in the same process only. We decide when the skeleton shows if plain Python is sufficient.
- The model of each route stays open (decision 10, due Tue 9/29). *Updated 10/2:* closed by [016](016-router-models.md).
- The frontend is a separate decision ([006](006-frontend.md)).
