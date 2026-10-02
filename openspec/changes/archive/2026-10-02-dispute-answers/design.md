# Design

## Context

The loop returns a `TurnOutput` whose `reason` is a policy `rule_id`; `demo_chat.py` maps it to a translation key (`_TEXT_KEYS`, `_HANDOFF_KEYS`) and the page renders the key from `app/static/i18n/*.json`. The conversation state is a dataclass stored as JSON (`app/state/conversation.py`), read with defaults, so new fields are backward compatible. Customer texts must not carry the window number (`tests/test_policy_texts.py`). The `YAML` country files hold values; the `texts:` block in them is not read by the loader, so locale files are the only source of customer text. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- A why follow-up answers from the decision the customer already saw, in the same language, with no model call.
- Every number in an explanation comes from the country file or a verified candidate.
- Safety rules reveal nothing about their criteria.

**Non-Goals:**
- Changing the policy engine's rules, values or order.
- Reading the customer's reason question with the model; that waits for prompt v3.
- Removing the dead `texts:` blocks from the YAML files or the repeated `person.insist` branch in the engine; noted, separate cleanup.

## Decisions

**1. Store a snapshot, do not recompute.** The state keeps `last_decision` with `rule_id`, `candidate_id`, `policy_version` and the values used (window days, charge date, last eligible date, age in days, synthetic flag). Recomputing at explanation time could contradict what the customer saw if the candidate list or the policy changed in between. Alternative: recompute from the current policy; rejected for that reason, and it would also call the engine on a turn that decides nothing.

**2. Recording point is `_hit`/`_from_hit`.** Every policy decision already passes there, so one write covers all rules. The decision is recorded only for rules that have an explanation kind; confirmations and case creation do not overwrite it.

**3. Explanation kinds live in code, keyed by `rule_id`.** Three kinds: `rule` (window, status, already disputed: rule plus values), `withheld` (amount.high, fraud.score, fraud.claim: one fixed key) and `none` (no decision). Country files keep values only. Alternative: a `rules:` block in each YAML naming the kind; rejected because the set is small, a bank edits values and not kinds, and a config error could turn a safety rule into one that discloses.

**4. Deterministic recognition of "why", gated by a stored decision.** A small per-language pattern set (es-419, pt-BR) that fires only when `last_decision` exists and the message asks a reason, and only if no charge is named in the message. A false positive costs a harmless explanation of something the customer just saw; a false negative falls through to the existing path. Alternative: a new router intent; rejected because it changes the measured router and the labels of `eval-v7`. Prompt v3 may learn it later and replace the patterns.

**5. New reply variant `explanation`.** It carries `message_key`, `rule_id` and a small map of verified values; the page fills placeholders in the locale text. Alternative: reuse `text`; rejected because `text` has no values and the window number would have to be written in the locale file, which a test forbids.

**6. Fixed sentence for all three safety rules.** One key serves `amount.high`, `fraud.score` and `fraud.claim`, so the answer does not say which rule fired (decision 010: the customer never sees the word fraud).

**7. Demonstration label is read from `synthetic`.** The explanation shows the label when the country file says `synthetic: true`, so a bank that sets it to false removes the label without code.

## Risks / Trade-offs

- **Pattern recall.** Phrasings outside the pattern set are not recognised. Mitigation: development cases per language, including colloquial forms; measured recall is reported with n, not assumed.
- **Pattern precision.** "¿Por qué?" mid-conversation could refer to something else. Mitigation: the explanation is about the last decision shown and is harmless.
- **Probing safety rules.** Mitigated by the fixed sentence and new adversarial attacks; zero unsafe outcomes is still a bound on a small sample, not zero risk.
- **pt-BR wording is not checked by a native speaker.** Same limit as [017](../../../docs/build/decisions/017-portuguese.md); wording is back-translated.
- **Demo policy is explained as a rule.** The label says so, but the 90 days still has no verified source ([021](../../../docs/build/decisions/021-dispute-policy-sources.md)); the explanation will read the real value the day the file changes.
