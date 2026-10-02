# Design

## Context

Prompt v2 (`app/ai/llm.py`) lists the four intents without definitions and carries eight development examples, none of them an opener. The runner seals a set by hash (`eval/seal.py`), refuses a second measurement of a measured hash (`eval/measured.json`), and freezes runs write-once. `eval-v7` measured baseline, v1 and v2 on 280 main cases; its system block does not replay offline, which `resolution-eval` investigates. The app serves v2 from the environment and fails at startup if its examples do not load (`app/ai/serving.py`). The detailed step order is in `team/router-v3-plan.md`. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- The opener gap is measured on a set that contains openers, against v2 and the baseline, with rules fixed first.
- v3 replaces v2 only on evidence.

**Non-Goals:**
- More intents, slots or wording by the model; they stay in `team/chat-behavior-plan.md`.

## Decisions

**1. Greetings map to `missing`.** The reply to `missing` already asks what the customer needs, which is the right answer to "hola". Alternative: a new `chitchat` label with friendly replies; rejected here because it changes the label set, the reply contract and every measured comparison.

**2. No code guard for openers.** A keyword guard would turn real out-of-scope requests without keywords into clarifications (15 of 39 development cases) and would hide what v8 measures. Checks for security (prompt extraction, injection record) are separate and do not touch intent.

**3. Amendment before any v3 number.** Metrics added: unnecessary-handoff rate (turns ending in a handoff or offer when the expected outcome is not one) and system outcome match. Gates kept: 0 unsafe on attacks, 0 missed transfers, no loss on v7 categories beyond the interval. Targets for the new metrics come from development numbers of baseline and v2, set before v3 runs on the sealed set.

**4. Sizing as in v7.** About 70 bases times four variants, with openers as at least one fifth of the bases, so the opener category alone has an interval narrow enough to decide; otherwise labelled descriptive.

**5. Same settings as v7.** GLM 5.3 Flash on both routes, reasoning low, 400 tokens, temperature 0, same seed and cluster bootstrap; spend cap fixed in the amendment.

**6. Freeze after the loop settles.** The v8 seal and measurement wait for the loop changes in flight, and the run records the commit it measured, so a later replay mismatch can be traced.

## Risks / Trade-offs

- **Time.** Cases, isolated authoring, review, sealing and a measurement take more than a day; if the submission comes first, v2 stays served with the opener limit declared.
- **Model-written cases.** Same provenance limit as v7: one model family writes and reviews; stated.
- **Regression on v7 categories.** Mitigated by the gate; failing it keeps v2.
- **Prompt length.** More definitions and examples raise cost and latency; both are reported, with the v7 numbers beside them.
