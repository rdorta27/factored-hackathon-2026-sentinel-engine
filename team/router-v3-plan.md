# Plan: router v3 and a new held-out measurement (eval-v8)

Status: proposed, not started; folded into [chat behaviour](chat-behavior-plan.md) as its first step. Date: 2026-10-02. Owner: Rubén.
Requirements: REQ-0016, REQ-0017, REQ-0019, REQ-0020, REQ-0047.

## Why

Serving router_v2 showed a case the evaluation never measured: a greeting
("hola", "hola, me llamo Karl") is classified `out_of_scope` by GLM 5.3 Flash
with prompt v2. The prompt names the four intents but never defines them, and
the eight v2 examples contain no greeting. The sealed set of 2024Q4-eval-v7
has no greeting-only or small-talk case, so its 0.98 says nothing about the
most common first message of a chat.

Already done on `feat/serve-router-v2` (code, no new measurement needed):

- **A.** Out of scope explains and offers an advisor first ([008](../docs/build/decisions/008-account-inquiry-scope.md)); two out-of-scope turns in a row get the offer and the third hands off; asking for an advisor hands off at once. A model mistake now costs a sentence, not a ticket.
- **D.** Names the customer introduces ("me llamo Karl") are masked before the model call (REQ-0047).
- **E.** "Who answered" is kept per thread, so the turn log cannot attribute a turn to another request's model.

B and C below are what A, D and E do not fix: the classification itself and
the evidence behind it.

## C. Evaluation (written first; the order is the proof, as in 018)

1. **Inventory the gap.** List the first-message types a chat receives that no case covers. Starting list:
   - greeting alone ("hola", "buenas", "oi", "olá");
   - greeting with a name ("hola, me llamo Karl");
   - courtesy and closing ("gracias", "chau", "obrigado");
   - small talk and identity ("¿cómo estás?", "¿eres un bot?");
   - empty or meaningless text ("???", emoji, "asdf");
   - generic help ("necesito ayuda");
   - greeting followed by a real request, which must keep its own intent;
   - out of scope without a baseline keyword (loan, address change, savings account, transfer not received, "¿cuánta plata tengo?"): 15 of 39 development `out_of_scope` cases have none.
2. **Add development cases** for every type, in the four variants (es-MX, es-CO, es-AR, pt-BR), with the expected intent and the expected system outcome (clarification, offer, handoff). Development split only.
3. **New metrics**, written into an amendment to [018](../docs/build/decisions/018-evaluation-acceptance.md) before any number exists:
   - *unnecessary handoff rate*: turns that end in a handoff although the expected outcome is not a handoff. 018 only counts missed transfers, and the two errors cost differently;
   - *system outcome match* alongside intent accuracy, since A changes what an intent leads to;
   - per-category accuracy for the new categories, with the same confidence intervals as today.
4. **Acceptance rules**, fixed with the amendment: v3 must keep every v7 gate (0 missed transfers, 0 unsafe on attacks) and must not lose accuracy on the v7 categories beyond the interval; the unnecessary handoff rate target is set from the development numbers of baseline and v2, before v3 is run on the sealed set.
5. **Write a new held-out set** with the same categories, by someone who has not seen v3 or its examples (the v7 review used an isolated subagent; repeat that and record it). Seal it with `python3 -m eval.seal`: a new hash, distinct from `27ad2f1b…`, which stays in `eval/measured.json` untouched.
6. **Measure once** as `2024Q4-eval-v8`: baseline, v2 and v3 on the same sealed set, same seed and settings as v7 (reasoning low, 400 tokens, temperature 0). v2 enters so the greeting gap shows with numbers. Freeze with `freeze.py`; never edit the run.

## B. Prompt v3 (designed on development only)

1. **Define the intents** in the system prompt, in one line each:
   - `charge`: the customer names a charge, debit or movement they want reviewed;
   - `missing`: the customer has not said what they need yet (greeting, introduction, thanks, "I have a problem", "help");
   - `out_of_scope`: they ask for something else from the bank (balance, loan, card, address, products);
   - `person`: they ask for a human.
2. **Examples:** keep the eight v2 ids and add the minimum that covers the new categories (a greeting alone, a greeting with a name, a closing), all from the development split and built by `eval/examples.py` (it refuses held-out ids). The ids go in `eval/examples_v3.json`.
3. **Iterate on development** until the new development set passes; no sealed case is read at any point.
4. **Do not add a code-side guard** on `out_of_scope`: 15 of 39 development out-of-scope cases carry no baseline keyword, so a keyword guard would turn real out-of-scope requests into clarifications.
5. **Serve v3 with the same guarantee as v2:** `SENTINEL_LLM_PROMPT_VERSION=v3` loads its examples through the same loader and fails at startup if they do not load; a test pins the example ids to those recorded in the eval-v8 summary.

## Order and dependencies

| # | Step | Needs |
|---|---|---|
| 1 | Inventory and development cases (C1, C2) | nothing |
| 2 | Amendment to 018: metrics, rules, targets (C3, C4), committed | step 1 |
| 3 | Prompt v3 on development (B1 to B3) | step 1; independent of 2 |
| 4 | Held-out set written and sealed (C5) | steps 2 and 3 frozen; author has not seen v3 |
| 5 | Measure eval-v8 once (C6) | step 4 |
| 6 | Serve v3, docs, requirement statuses (B5) | step 5 |

Until step 5 the served app runs v2 with A, D and E, and says so in the README
limitations: a greeting alone is classified out of scope and now gets an offer,
not a ticket.

## Open decisions

- **Schedule.** [`team/tasks.md`](tasks.md) freezes code and results on Fri 10/2 and submits Sat 10/3 to Mon 10/5. This plan does not fit before that. Either it lands after submission (and the submission cites eval-v7 for v2 plus the limit above), or the freeze date moves. Owner to decide.
- **Author of the new held-out set** and how the review is recorded.
- **Budget:** the cap for the eval-v8 run (v7 cap in `eval/budget.py` as reference).
