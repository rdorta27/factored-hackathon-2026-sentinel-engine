# Design

## Context

`extract_facts` and `ground` in `app/ai/grounding.py` select a charge only on an exact match of every stated fact (full merchant name, ISO or "15 de enero" dates, exact amount) and otherwise return every row; `rank_candidates` orders by exact hits and age. `step` in `app/orchestrator/step.py` receives masked text, calls `ports.model.understand`, then `ports.tools.lookup_transactions()` (no time limit, `SessionBoundLookup` in `app/tools/bound.py`). Out-of-scope turns answer with an offer and the third in a row hands off (`MAX_SCOPE_OFFERS = 2`). Three failed lookups hand off without a case number (`MAX_ATTEMPTS = 3`). Step records accept `timeout` as outcome. A3, A4b and D4 are `xfail(strict=True)` and assert fields the strict reply schema does not have (`policy`, `injection_detected`). The sealed set of `eval-v7` holds four extraction attempts labelled handoff and five mixed injection-plus-charge messages labelled clarification. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:** the shown list reflects what was said; the three attacks are blocked or recorded in code; nothing measured changes its label.

**Non-Goals:** changing what the model is asked.

## Decisions

**1. Exact facts select, soft facts only narrow.** `ground` keeps its contract; a new narrowing step applies soft facts (merchant tokens, relative dates, repeated charges) to the candidate list. A single soft match is still a clarification.

**2. Merchant tokens.** Accent- and case-normalised tokens, stop words dropped ("la", "el", "de", "do", "da", "na"), match by equality or a shared prefix of four or more letters.

**3. Relative dates.** A per-language table maps hoy/hoje 0, ayer/ontem 1, anteayer/anteontem 2, weekday names to the latest past day, "semana pasada"/"semana passada" to the previous seven days, "hace N días"/"há N dias" to N; the reference date comes from the policy.

**4. One guard module, two pattern sets.** Extraction (reveal/repeat/copy plus prompt, instructions, configuration; voseo forms such as "Copiame") and injection (ignore instructions, skip confirmation, admin or system mode, fake tags). Both run on masked text before the model, accent-insensitive, with negative sets.

**5. Extraction answers as an out-of-scope offer with its own key.** It increments `scope_asks`, which keeps decision 008's path and matches the four sealed handoff labels (an offer satisfies a required transfer in `match_outcome`). Messages that also name a charge skip the refusal, so the five mixed sealed cases keep their clarification label; replies carry keys only, so serving the charge discloses nothing.

**6. Injection is recorded, not blocked.** Blocking would change measured replies and adds little over the closed labels and the structured confirmation.

**7. Read budget in the tool layer.** `SessionBoundLookup` runs reads in a small worker pool with `future.result(timeout=...)` from `SENTINEL_GOLD_TIMEOUT_S` (default well above the measured 0.28 s cold read); a timeout emits a `timeout` record and raises the failure the retry path already handles.

**8. Tests rewritten to the contract.** A3 asserts the refusal key and the `extraction_refused` record; A4b the `injection_suspected` record and no case; D4 a handoff within a small budget. All drop `xfail` and move to `blocked_verified`; one adversarial run is frozen at the end.

## Risks / Trade-offs

- **Loose narrowing could hide the right charge:** four-letter prefix minimum and a row is dropped only when a stated detail contradicts it; tests over every mock merchant.
- **Pattern recall:** unlisted phrasings reach the model, which still cannot leak through the key-only replies; documented.
- **False positives:** negative sets for "sistema", "instrucciones para disputar".
- **Background work after a timeout:** Gold is read-only; a bounded pool limits threads.
- **Measured runs:** `2024Q4-resolution-v1` measured the old list; `evaluation-final` re-measures after this lands.
