# Plan: a chat that behaves better

Status: proposed, not started. Date: 2026-10-02. Owner: Rubén. No time limit
set for this work (the Sunday 10/4 freeze in [tasks](tasks.md) is lifted for
it; the owner decides what is in the submission). Supersedes the prompt part
of [router v3](router-v3-plan.md), which becomes step 1 here.
Requirements: REQ-0001, REQ-0002, REQ-0016, REQ-0017, REQ-0044, REQ-0047.

## What the chat does today (probe, 2026-10-02, router_v2, real model)

Sixteen synthetic first messages, one fresh session each, mock Gold:

| Message | Answer | Problem |
|---|---|---|
| "hola", "gracias", "¿eres un bot?" | "I can only help with charges…" | small talk is treated as out of scope |
| "no reconozco un cargo de Tienda Lumbre", "me cobraron dos veces en la cafetería ayer", "hay un cobro de 849…", "el de ayer", "oi, não reconheço… R$ 215" | the same three chips (the newest charges) | what the customer said never narrows the list |
| "quiero ver el estado de mi último cargo" | which charge? | a status question is not understood as one |
| "no fui yo, alguien usó mi tarjeta" | the same chips | the claim is registered but the answer does not change |
| "hola, tengo un problema… no sé cómo explicarlo" | the same chips | no guidance on what to say |

Two causes. The model returns one label (and an `amount` the code ignores), and
the code finds the charge with regex parsers (`app/ai/grounding.py`) that need
an exact merchant name and understand dates only in some phrasings. The
replies are translation keys, so every situation gets one fixed sentence.

## Principles that do not change

- The model understands; code decides and verifies. Policy, eligibility, the
  confirm box, idempotency and the handoff stay in code.
- The model never sees `customer_id` or any identifier; free text is masked.
- A model claim about a charge counts only if it matches a verified candidate.
- Replies carry keys and verified values, never model prose (the `chat` contract),
  unless the owner accepts step 5.
- A model failure answers the turn with the baseline, never an error.

## Steps

1. **A richer reading, one call.** The model returns, in the same call:
   - `intent`: charge, status, missing, chitchat, out_of_scope (with a subtype: balance, loan, card, address, other), person;
   - `not_mine`;
   - slots as the customer said them: merchant words, amount, a date phrase, and whether they say it happened twice.
   The prompt defines every intent and each slot, with development examples
   (greeting, thanks, "are you a bot", status, a vague complaint). Output stays
   JSON mode, reasoning low, bounded tokens.
2. **Grounding with the reading.** Code turns the date phrase into a date from
   the reference date, resolves merchant words against the real candidates (fuzzy,
   accent-insensitive: "cafetería" finds "Cafe Central"), and keeps the existing
   regex parsers as a cross-check. A slot that matches no candidate is dropped, so
   a wrong model slot cannot pick a charge. One match goes to the confirm box;
   several matches show only those; none shows the list and says nothing was found.
3. **Behaviour by situation, in code:**
   - chitchat: a friendly reply by subtype (greeting, thanks, "are you a bot": yes, an assistant for charge disputes) and what it can do next, never a handoff;
   - status: answer from the verified candidate (status, date, whether it can be disputed) without opening a dispute;
   - missing: ask for the one thing that is missing (which charge, amount or date), with chips when useful;
   - out of scope by subtype: say what is not possible and what is, then the advisor offer; the third turn in a row hands off, and a request for an advisor hands off at once (already built);
   - corrections ("no, el otro", "era ayer") use the turns and the candidates already shown.
4. **Varied but fixed wording.** Several reviewed variants per key and per
   language (es-419, pt-BR), picked by a deterministic rule from the turn count so
   the answer is reproducible, with verified values (merchant, amount, date)
   inserted from the candidate, never from the model. Same register as the
   [conversation rules](../docs/build/conversation.md).
5. **Optional, needs a decision: model-written wording** for non-decision turns
   only (greeting, small talk, clarifying questions, out-of-scope explanations).
   Constrained by schema, language and length; it may not contain figures, names
   or promises that are not in the verified facts; any validation failure uses the
   step 4 template. It reads more naturally, changes the `chat` contract
   (keys only) and decision 007, adds an injection surface, and needs its own
   measurement. Recommended only after steps 1 to 4 are measured.
6. **Evaluation by conversation, not only by intent** (amendment to
   [018](../docs/build/decisions/018-evaluation-acceptance.md) before any number):
   - cases are short dialogues (1 to 4 turns) in es-MX, es-CO, es-AR and pt-BR, labelled with the right charge, the expected outcome and whether a handoff is right;
   - metrics: right charge found, turns to reach it, unnecessary handoff rate, missed transfers (still 0), unsafe outcomes (still 0), clarification rate, language kept, latency p50/p95 and cost per turn;
   - no LLM judge: labels come from the case design, so REQ-0023 stays not applicable;
   - a new sealed held-out set written by someone who has not seen the prompt, a new seal hash, one measurement (`2024Q4-eval-v8`) of baseline, router_v2 and the new reading on the same set; `eval/measured.json` keeps the v7 hash untouched.
7. **Serve it** with the same guarantee as v2 (examples loaded through the
   eval loader, startup fails otherwise, a test pins the example ids to the run's
   summary), update the README limitations, the requirement statuses and the
   decisions (007 and 016 annexes).

## Order

1 and 6 (cases first) → 2 → 3 → 4 → freeze the rules in 018 → write and seal
the held-out set → measure once → 7. Step 5 only after that, as its own change.

## Risks

- **Latency and cost:** a longer prompt and output. Budget: p95 under about 5 s per turn, cost per turn within 2x of v7; both measured.
- **Wrong slots:** mitigated by grounding against verified candidates only.
- **Over-fitting to the probe:** the sixteen messages above are not test cases; the cases are written by category and sealed before the model sees them.
- **pt-BR quality:** the team has no Portuguese speaker; wording variants are back-translated as in [017](../docs/build/decisions/017-portuguese.md).

## Open decisions

- Accept step 5 (model-written wording) now, later or never.
- Who writes the sealed dialogues and how the review is recorded.
- Budget cap for the eval-v8 run.
