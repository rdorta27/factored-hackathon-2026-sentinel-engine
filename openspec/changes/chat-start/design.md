---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Openers are code, after the router.** The router keeps four labels plus `status` (router v3). A greeting is `missing`. A short list of patterns in es-419 and pt-BR picks the subtype: greeting, thanks, goodbye, identity. The patterns run only on `missing` and only on short messages, so a greeting followed by a request keeps its own intent.
2. **Status answers do not change state.** The status reply reads the verified candidate and the case store. It never opens the box.
3. **The why answer reuses the explanation module.** A named charge goes through the policy engine without the box. The answer cites the rule id and its values, the same as `decision-explanation`.
4. **Parsers stay deterministic.** Amounts in words use a small number grammar (units, tens, hundreds, "mil") in Spanish and Portuguese. Date phrases resolve against the reference date. A parsed value that matches no candidate is dropped.
5. **Wording variants are reviewed text.** Each key has variants in es-419 and pt-BR. The index is `turn_count mod n`, so a replay gives the same text.

## Risks

- The opener patterns can hide a real request. Mitigation: only on `missing`, only below a length limit; tests with greeting-plus-request cases.
- Frozen replays can change. Mitigation: run `verify` on `2024Q4-resolution-v2`; freeze a new run if it changes.
