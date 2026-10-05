---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **The handoff reference belongs to the case, not to the session.** The state keeps the reference of each filed ticket and the charge that it covers. A new message goes through the loop. If it names the charge of a filed ticket, or asks for a person again, the reply is the "case with an advisor" text with that reference. Otherwise the loop continues.
2. **The ticket reason is fixed at file time.** Later turns never write the `reason_key` of a filed ticket.
3. **Dispute status is a code check, like the prompt-extraction refusal.** A short list of phrases in es-419 and pt-BR (`en qué va`, `estado de mi disputa/reclamo`, `ya abrí`, `meu reclamação`, `status da contestação`). It runs before the model and before the confirm box. It reads only the cases of the session customer. It does not change the baseline or the router.
4. **The box yields to a correction.** With a box open, the loop runs the narrowing parsers on the message. If they ground a different candidate, the box closes, and the loop shows the new candidate in a new box. A confirm carries the candidate id of the box that the customer saw, so a stale confirm is refused (the existing token rule).
5. **Already disputed before the box.** The check uses the case store, the same as the API, before the box opens.

## Risks

- The status phrases can catch a new request. Mitigation: a phrase must also say "already" or "status"; tests in both languages, with negative cases.
- A frozen replay can change. Mitigation: run `verify` on `2024Q4-resolution-v2`; if it differs, freeze `2024Q4-resolution-v3` with the reason.
