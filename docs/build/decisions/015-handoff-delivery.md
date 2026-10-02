# 015 · Handoff delivery: ticket store now, queue to the CRM in production

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 28.

## Context

The brief asks for a structured handoff to a person with the request, verified facts, actions and open questions (REQ-0008). The demo already files every handoff as an escalated ticket in the SQLite case store and shows it in a read-only advisor view ([009](009-demo-ui-and-advisor-view.md)). What was open is how the package reaches advisors in a real bank. Routing by language and specialty is REQ-0046 (P2, simulated).

## Options

1. **Build a queue now:** adds infrastructure the demo does not need and cannot show better than the advisor view.
2. **Keep the ticket store in the demo and specify the production channel.**

## Decision

Option 2.

- **Demo:** handoff → ticket in the case store → read-only advisor view (`GET /api/v1/handoffs`). Built and tested.
- **Production:** the same ticket is published to a queue (for example Azure Service Bus), and a consumer creates it in the bank's CRM or ticketing system, routed by language and specialty (REQ-0046). The package format does not change, so the advisor sees the same content.

## Consequences

- The demo keeps a working human-in-the-loop path with no extra infrastructure.
- A queue decouples the assistant from the CRM: if the CRM is down, tickets wait instead of being lost.
- Listed as remaining deployment work in the [path to production](../../architecture/specification.md#path-to-production).
