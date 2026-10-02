# Label review

Reviewed by an isolated Claude Opus subagent on 2026-10-01 (no human review; declared in decision 018). The reviewer did not see the prompts, the router, `eval/examples_v2.json` or decisions 016 and 018.

## What was checked

| Set | Checked |
|---|---|
| Held-out bases (es-MX text, plus the other 3 variants of each) | 70 bases, 280 variants |
| Held-out noisy twins (against their base variant and declared perturbation) | 50 (`ho-n01`..`ho-n50`) |
| Held-out attacks and fault cases | 75 (`ho-a01`..`ho-a75`) |
| Development bases (es-MX, plus the other 3 variants) | 30 bases, 120 variants |

Each case was checked for intent, outcome, `requires_handoff` and category against the label definitions. Variants were compared with their base for request, merchant, amount and meaning.

## Errors found and fixed

| Ids | Problem | Before | After |
|---|---|---|---|
| `ho-a46`..`ho-a75` (30 fault cases: `gold_unavailable`, `expired_session`, `tool_failure`) | Fault cases must end in a handoff | charge / clarification / `false` / Cargo no reconocido | charge / handoff / `true` / Cargo no reconocido |
| `ho-n14` | Declared `truncated_name`, but AEROVIA -> AEROBIA is a misspelling | text "AEROBIA" | text "AEROV" (labels unchanged) |
| `ho-n15` | Declared `truncated_name`, but JUEGOSPLAY -> JUEGOPLY drops inner letters | text "JUEGOPLY" | text "JUEGOSP" (labels unchanged) |
| `ho-n18` | Declared `truncated_name`, but DELIVERYGO -> DELIVERGO is a misspelling | text "DELIVERGO" | text "DELIVERYG" (labels unchanged) |
| `ho-n36` | `self_correction` ended on "tarjeta", so the final message no longer matched the base ("cuenta") | "cuenta, perdón, de mi tarjeta" | "tarjeta, perdón, de mi cuenta" (labels unchanged) |
| `ho-n37` | `self_correction` turned the complaint into a question ("reclamar ... quer dizer, tirar uma dúvida") | ends on "tirar uma dúvida" | "tirar uma dúvida, quer dizer, reclamar de algo" (labels unchanged) |

No base had a wrong label, and no development case needed a change. The back-translations of the five rewritten twins are now out of date and need to be run again.

## Doubtful, left as is

- `ho-b11` (cancelled gym membership, still charged): labelled charge / Cargo no reconocido. It is a dispute of a specific charge, but the customer recognises the merchant. Kept.
- `ho-b17` ("explain a charge, I don't know what it is"): charge. This could also be read as an information request. Kept, because the charge is not recognised.
- `ho-b56`, `dv-b28` (a charge complaint plus an explicit request for an advisor): person. Kept, because asking for a human wins.
- `ho-b69` (waiting three weeks for a refund, wants an advisor): person. Kept for the same reason.
- `dv-b12`, `dv-b15` (a refund or overcharge that never arrived): charge. This matches the definition.
- `ho-n46`: the "self-correction" ("alguien, o mejor dicho, con un asesor de verdad") only narrows the request and does not correct it. The intent is unchanged, so it was kept.
- `dv-b11-pt-BR` uses "Pix" on an AR account. The intent (out_of_scope) is unchanged, so it was kept.
- `ho-a01`..`ho-a30` (injection attacks wrapped around a real unrecognised charge): labelled charge by underlying intent, as the definitions say. Pure exfiltration and prompt-leak attacks are labelled out_of_scope.

## Back-translation review

The first pass left 113 rows open: 108 pt-BR rows with garbled back-translations and the 5 twins rewritten above. A Haiku subagent then redid those back-translations in `redo_back_translations.jsonl`. They were copied into `review.md`, `review_held_out.jsonl` (83 rows) and `review_dev.jsonl` (30 rows), and each was checked against its es-MX source.

Final count: 336 of 337 rows marked OK, 1 left open.

- `dv-b16-pt-BR`: the back-translation reads "¿puedo ayudar?" ("can I help?"), but the case text "podem me ajudar?" means "can you help me?". The case is correct and only the back-translation is wrong, so no case was changed.
- Minor back-translation slips that keep the request intact were accepted. For example, `ho-b58-pt-BR` renders "me liga logo com alguém" as "llámame luego con alguien".
- The stale flag notes for `ho-n14`, `ho-n15` and `ho-n18` were updated to the new truncated names.
