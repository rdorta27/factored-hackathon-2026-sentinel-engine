# Proposal

## Why

A greeting ("hola", "hola, me llamo Karl", "oi") or small talk ("gracias", "¿eres un bot?") is classified `out_of_scope` by the served router_v2, so the first message of most chats gets "I can only help with charges" and the advisor offer ([router v3 plan](../../../team/router-v3-plan.md)). The prompt never defines its four intents, the v2 examples hold no greeting, and the sealed set of `2024Q4-eval-v7` has no opener, so its 0.98 says nothing about them. A keyword guard in code would hide the gap instead of measuring it (REQ-0016, REQ-0017, REQ-0020).

## What Changes

- **Cases first:** development cases for every uncovered first-message type in es-MX, es-CO, es-AR and pt-BR, with expected intent and system outcome.
- **Rules before numbers:** the 018 amendment of `router-confidence` is extended with the unnecessary-handoff rate and the system outcome match, every v7 gate kept, targets from development numbers.
- **Prompt v3:** one line per intent (greetings, thanks and "I have a problem" are `missing`), the v2 examples plus the fewest new development examples; development only. *Updated 2026-10-04:* v3 adds one label, `status`, for a question about the status of a charge. [`chat-start`](../chat-start/proposal.md) answers it in code. A question about the status of a dispute stays a code check in [`flow-fixes`](../flow-fixes/proposal.md).
- **Cut-offs re-fitted on v3** with the code and rule of `router-confidence`, since v3 changes the label distribution.
- **One sealed set** by an isolated author, reviewed and back-translated as in v7: single-turn intent with openers **and multi-turn resolution** (select, confirm, verified case number, or the refusal or handoff the policy requires).
- **One measurement, `2024Q4-eval-v8`:** baseline, the trained baseline of [`trained-baseline`](../trained-baseline/proposal.md), v2, v2 with cut-offs, v3 and v3 with cut-offs, same settings as v7, under a spend cap, broken down by language and country. The best candidate that passes every gate is served; otherwise v2 stays and the result is reported. The resolution block measures the loop after `flow-fixes` and `chat-start` merge.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `llm-router`: a prompt version that defines each intent and covers openers, served only after it passes the amended rules.
- `sealed-case-set`: a second sealed set for `eval-v8` with openers and multi-turn resolution.

## Impact

- `sentinel-ai-core/app/ai/llm.py` (prompt v3), `eval/examples_v3.json`, development and sealed cases, `eval/measured.json` (appended), new runs under `evidence/evaluation-runs/`, the 018 amendment, the metrics report, README, REQ-0016 evidence.
- Not changed: `eval-v7`, its seal entry, the policy engine, the reply contract.

## Non-goals

- New labels other than `status`, or model-extracted slots.
- Model-written replies, or a different model ([016](../../../docs/build/decisions/016-router-models.md)).

## Assumptions

- `evaluation-final`, `router-confidence` and `ui-product` are in `main` (PRs #55 to #57). `flow-fixes`, `chat-start` and `trained-baseline` merge before the seal.
- The 14 situations of `resolution-v1` guide the isolated author, never as cases.
- The owner fixes the spend cap and the author before sealing.
