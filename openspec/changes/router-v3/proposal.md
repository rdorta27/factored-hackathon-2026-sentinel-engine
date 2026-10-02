# Proposal

## Why

Serving router_v2 showed a gap the measurement never covered: a greeting ("hola", "hola, me llamo Karl", "oi") or small talk ("gracias", "¿eres un bot?") is classified `out_of_scope`, so the first message of most chats gets "I can only help with charges" and the advisor offer ([router v3 plan](../../../team/router-v3-plan.md)). The prompt names four intents but never defines them, the eight v2 examples hold no greeting, and the sealed set of `2024Q4-eval-v7` has no opener, so its 0.98 says nothing about them. Fifteen of 39 development out-of-scope cases also carry no baseline keyword. A keyword guard in code would hide the gap instead of measuring it (REQ-0016, REQ-0017, REQ-0020).

## What Changes

- **Cases first:** an inventory of first-message types no case covers (greeting alone, greeting with a name, courtesy and closing, small talk and identity questions, empty or meaningless text, generic help, greeting followed by a real request, out of scope without a keyword), written as development cases in es-MX, es-CO, es-AR and pt-BR with the expected intent and system outcome.
- **Rules before numbers:** an amendment to [018](../../../docs/build/decisions/018-evaluation-acceptance.md), committed before any v3 number, adds the unnecessary-handoff rate and the system outcome match, keeps every v7 gate, and sets targets from development numbers.
- **Prompt v3:** one line per intent (greetings, thanks and "I have a problem" are `missing`), the eight v2 examples plus the fewest new development examples needed; iterated on development only.
- **New sealed set:** written by an author isolated from the prompt, examples and rules, reviewed and back-translated as in v7, sealed under a new hash.
- **One measurement, `2024Q4-eval-v8`:** baseline, v2 and v3 on the same sealed set, same settings as v7, under a spend cap.
- **Serve v3** with the same guarantees as v2 if it passes the rules; otherwise v2 stays served and the result is reported.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `llm-router`: a prompt version that defines each intent and covers openers, served only after it passes the amended rules.
- `sealed-case-set`: a second sealed set for `eval-v8`, isolated from v3, with openers.

## Impact

- `sentinel-ai-core/app/ai/llm.py` (prompt v3), `eval/examples_v3.json`, development and sealed cases, `eval/measured.json` (appended), a new run under `evidence/evaluation-runs/`, decision 018 amendment, the metrics report, README, REQ-0016 evidence.
- Not changed: `eval-v7`, its seal entry, the policy engine, the reply contract.

## Non-goals

- New labels such as `chitchat` or `status`, or model-extracted slots; the label set stays closed at four.
- Model-written replies.
- Changing the served model; GLM 5.3 Flash stays ([016](../../../docs/build/decisions/016-router-models.md)).

## Assumptions

- `chat-loop`, `real-gold` and `evaluation-final` land before the v8 seal, so v8 measures the loop that is served; the resolution set of `resolution-eval` is re-run on v3 in the same measurement.
- The spend cap and the author of the sealed set are fixed by the owner before sealing.
