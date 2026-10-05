---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

Felix tested the demo on `main` on 2026-10-04, as a customer, with a clean SQLite file and a new session for each test. Four flow defects make the demo fail in front of a customer. They do not depend on the model (REQ-0001, REQ-0002, REQ-0005, REQ-0006, REQ-0008):

1. After a handoff, every message returns the same ticket, also a new and valid request. The reason of the ticket changes between "person" and "missing data" (`app/routers/demo_chat.py`, `handoff_reference`).
2. "Ya abrí una disputa, ¿en qué va?" ("I already opened a dispute, what is its status?") starts a new dispute. The customer selected a charge and got a second case.
3. With the confirm box open, a correction ("no, perdón, el de 700") is ignored. The box keeps the first charge, so a confirm opens the wrong case (`app/orchestrator/step.py`: the box swallows every message except a person request).
4. The system offers the confirm box for a charge that already has an open dispute. It warns only after the confirmation.

Two smaller defects: "algo raro ayer" ("something odd yesterday") gives no clear answer when no charge matches the date, and Felix found no length limit on the message.

## What Changes

- **After a handoff:** a message about the same case answers "your case is with an advisor (`HO-…`)". A request about another charge continues the normal flow. The reason of a ticket does not change after it is filed.
- **Dispute status:** a deterministic check in code, before the model, recognizes a question about the status of an existing dispute in es-419 and pt-BR. It answers from the case store of the customer. If no case exists, it says so. It never opens a new case.
- **Correction with the box open:** a message that names another amount, merchant or date closes the box and grounds the new charge. A confirm always opens the charge shown in the current box.
- **Already disputed:** the warning comes before the box, and the box does not open.
- **No match for a date:** the reply names the date that it searched ("no charges on 16 Jun").
- **Length limit:** verify the 2000-character limit in the server, and add a test. The page already sets `maxlength="2000"`, and `bank-ui` owns `static/`.
- **Rate limit reply:** the 429 body carries the `trace_id`. The error bubble already shows it, and `bank-ui` owns `static/`.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `orchestrator-loop`: handoff state, dispute status, corrections with the box open, and the already-disputed check.

## Impact

- `sentinel-ai-core/app/orchestrator/step.py`, `app/routers/demo_chat.py`, `app/state/cases.py`, locale files, tests, `team/chat-manual-tests.md`.
- A new resolution run if a frozen replay changes (`2024Q4-resolution-v2` must still verify, or a new run explains why not).

## Non-goals

- Changes to the keyword baseline. `eval-v7` replays it, and Felix asks to keep it.
- Loans and amounts in words (Felix 4 and 8). They depend on the model: `chat-start` and `router-v3`.
- New UI. The charge states in the panel are in `bank-ui`.
