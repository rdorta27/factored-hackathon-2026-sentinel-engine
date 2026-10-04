---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 024 · The model writes the words of turns that do not decide

**Date:** 2026-10-04
**Status:** Accepted
**Participants:** Rubén (owner)

## Context

The router returns one label, the language and the "not mine" claim. Every reply that the customer sees is a fixed template. The result is a rigid chat:

- "hola" gets "I can only help with charges".
- A greeting, thanks or "are you a bot?" has no natural answer.
- The same sentence repeats in the same situation.

The manual test of Felix and the probe of 2026-10-02 show these gaps. The brief asks for an AI-first service, and the judges weigh the product and the pitch most.

Three constraints stay as they are:

- Code decides permissions, policy, confirmation and handoff (REQ-0007, REQ-0033, REQ-0048).
- Each datum that the customer sees comes from the source, not from the model. Diego (MLE at Factored) asked for this: "the data is injected, not assumed".
- The model receives the masked message only. It never receives identifiers, the fraud score or Gold rows ([what the model never receives](../../rationale/model-data-minimization.md), REQ-0047).

## Options

1. **Templates only.** The safest option. The chat stays rigid, and the model cannot improve what the customer reads.
2. **The model writes a draft with placeholders. Code fills the facts and validates the draft.** The reply sounds natural. The model never writes a value. A validator refuses any unverified datum.
3. **The model writes free text.** The most natural option. Nothing stops an invented amount, name, date or promise. It breaks the rule that the data comes from the source.

## Decision

**Option 2**, for turns that do not decide, and only there.

**Turns that may use a draft:** greeting, thanks, goodbye, "are you a bot?", generic help, a clarifying question, the explanation that a request is out of scope, and the answer to a charge status question.

**Turns that always use a template:** the confirm box, the case confirmation, a policy refusal, a handoff, an error, and the "why?" answer that cites a rule and its values.

**How a draft works:**

1. The model returns `reply_draft` in the same call that reads the intent. It contains placeholders only for values: `{merchant}`, `{amount}`, `{date}`, `{status}`.
2. Code fills each placeholder from the verified candidate of the turn. The model never sees the values.
3. A validator refuses a draft with: a digit outside a placeholder; an unknown placeholder; a name, merchant or date that is not in the verified facts; a promise (refund, time or result); a language that is not the reply language; or a length over the limit.
4. When the validator refuses a draft, the reply uses the template of the turn. The turn record shows `draft_rejected` and the reason.
5. The contract of the reply keeps `message_key` and adds an optional `text`. The page shows `text` when it exists.

**Safeguard:** `reply_draft` is an optional field of the router contract. If the human review of the chat finds that the drafts are not good enough, we remove the field. Nothing else in the plan changes, and the replies use varied templates.

## Consequences

- **Gain:** a chat that answers greetings and small talk in a natural way, in es-419 and pt-BR, and a clear pitch: the model writes the words, and the code writes the facts.
- **Cost:** a new surface for prompt injection (the model output is now shown). The validator, new adversarial tests and the evaluation cover it.
- **Evaluation:** `eval-v8` counts an unsafe wording (a shown text with a datum that is not verified) as an unsafe outcome, and reports the rate of rejected drafts. A draft that passes the validator must still have zero unsafe wording on the sealed set.
- **Cost and latency:** a longer prompt and a draft raise both. We report them beside the numbers of `eval-v7`.
- **Replay:** each live draft is recorded with the call, so an offline replay shows the same text.
- **Contract:** the `chat` contract changes from "keys only" to "keys and an optional validated text". Decision [007](007-learned-component.md) is updated.
- **Limit:** the keyword baseline writes no drafts. When the baseline answers, the replies are templates.
