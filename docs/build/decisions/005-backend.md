# 005 · Backend: Python, FastAPI (LangGraph deferred)

**Date:** 2026-09-28
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 9.

## Context

The Tuesday skeleton needs an HTTP API and an orchestrator. The team stack is Python. .NET is out. The loop is Understand → Decide → Act → Verify → Escalate, with policy, session and idempotency in code, not in the prompt (REQ-0007).

## Options

1. **Python + FastAPI, loop in plain Python.** Thinnest for Tuesday. The confirmation, retry and handoff path gets rewritten when the ambiguous case arrives.
2. **Python + FastAPI, LangGraph in the same process.** The graph is the loop only. Policy, the session and idempotency stay in code. One process to deploy.
3. **A separate LangGraph service, or a Node API.** A second process before Thursday's deploy, with no gain for four tools.

## Decision

Python with FastAPI. Decided now: language and framework. Deferred: whether the loop uses LangGraph or plain Python; the Tuesday skeleton starts with the thinnest loop that meets the contracts. Policy, the authenticated session and idempotency stay in code either way, and no orchestrator ever sees `customer_id`.

## Consequences

- The orchestrator can swap a mock tool for a real store without changing its protocol.
- LangGraph stays an option for the loop (in-process only); we decide once the skeleton shows whether plain Python is enough.
- Which model serves each route stays open (decision 10, due Tue 9/29).
- Frontend is a separate decision ([006](006-frontend.md)).
