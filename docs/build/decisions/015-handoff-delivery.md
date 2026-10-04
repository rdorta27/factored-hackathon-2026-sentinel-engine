---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 015 · Handoff delivery: ticket store now, queue to the CRM in production

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 28.

## Context

The brief asks for a structured handoff to a person, with the request, the verified facts, the actions and the open questions (REQ-0008). The demo already files every handoff as an escalated ticket in the SQLite case store. A read-only advisor view shows it ([009](009-demo-ui-and-advisor-view.md)). The open question was how the package reaches advisors in a real bank. Routing by language and specialty is REQ-0046 (P2, simulated).

## Options

1. **Build a queue now:** it adds infrastructure that the demo does not need. It cannot show more than the advisor view.
2. **Keep the ticket store in the demo and specify the production channel.**

## Decision

Option 2.

- **Demo:** handoff → ticket in the case store → read-only advisor view (`GET /api/v1/handoffs`). Built and tested.
- **Production:** the service publishes the same ticket to a queue (for example Azure Service Bus). A consumer creates it in the CRM or ticket system of the bank, routed by language and specialty (REQ-0046). The package format does not change, so the advisor sees the same content.

## Consequences

- The demo keeps a working human-in-the-loop path with no extra infrastructure.
- A queue separates the assistant from the CRM. If the CRM is down, tickets wait. They are not lost.
- The [path to production](../../architecture/specification.md#path-to-production) lists this as remaining deployment work.
