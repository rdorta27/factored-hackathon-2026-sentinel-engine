---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **The contract is the seam.** The loop reads contract v3 fields only through `UnderstandResult`. Each field is optional, so every behavior has a path for v2 and the baseline.
2. **Fallbacks stay out of the baseline.** Opener patterns and the amount and date parsers live in the orchestrator and `grounding.py`, not in `app/ai/demo.py`. The baseline labels stay the same as in `eval-v7`.
3. **Slots never select alone.** A slot narrows only among verified candidates. One match goes to the confirm box; several show only those; none says what was searched.
4. **Status and why do not change state.** They read the candidate, the case store and the policy result. They never open a box.
5. **Words by turn kind.** A table maps each reply kind to "draft allowed" or "template only". Confirm box, case confirmation, policy refusal, handoff and error are template only.
6. **Reproducible templates.** Variant index = turn count mod n, so a replay gives the same text.

## Risks

- Opener patterns can hide a request: only on `missing`, only on short messages, with greeting-plus-request tests.
- Frozen replays change: run `verify` on `2024Q4-resolution-v2` and freeze a new run if the change is intended.
- The draft adds an injection surface: the validator of `router-v3` and the adversarial suite cover it.

## Coordination with `flow-fixes` and `bank-ui` (2026-10-04)

7. **Merge `flow-fixes` first.** It extends `ExplanationValues` and `Clarification` with optional fields in `app/schemas/chat.py`. This change adds `text` beside them and does not change an existing field.
8. **Reuse the `explanation` kind for status and why.** The charge-status reply and the why-for-a-named-charge reply carry verified values (merchant, amount, date, status) in the existing values object, which the page already fills. No new reply kind.
9. **No HTML.** Only locale keys. `bank-ui` owns the page.
10. **Python.** If `python3 -m pytest` does not find pytest, use the full interpreter path in `.local/final-push/02-sesiones.md`. Run `uvicorn` on port 8004.
