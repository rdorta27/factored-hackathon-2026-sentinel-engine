# Proposal

## Why

The product is a dispute intake that knows when not to act. Two things weaken it on the first turns a person tries. First, it does not use what the customer says: different messages naming a merchant, a relative date or a repeated charge all show the same three newest charges, and a reply never says that nothing matched (MT-06, [chat plan](../../../team/chat-behavior-plan.md)). Second, three attacks have no defence in code in every adversarial run (latest `evidence/adversarial/20261002T195516Z/`): A3 (repeat your prompt), A4b (an injected instruction is not even recorded) and D4 (a slow Gold read holds the request open, which matters now that the app reads the real DuckDB file). The brief asks to clarify ambiguity, ground answers in permitted records, test prompt injection and tool failures, and bound retries (REQ-0002, REQ-0003, REQ-0021, REQ-0026, REQ-0033).

## What Changes

- **Narrowing:** candidates are filtered and ranked by what the customer said: merchant words matched accent-insensitively by token or prefix, relative dates from the reference date in es-419 and pt-BR, and repeated-charge phrasing. A reply says when stated details matched nothing. Narrowing never opens the confirm box by itself.
- **A3:** a deterministic check before the model refuses requests to reveal or repeat the prompt or instructions, with the out-of-scope offer, logged as `extraction_refused`; a message that also names a charge follows the normal path.
- **A4b:** injection patterns are recorded as `injection_suspected` without changing the reply.
- **D4:** Gold reads run under a time budget; a timeout is a failed attempt in the existing bounded retry and ends in the handoff path.
- One new adversarial run with A3, A4b and D4 in `blocked_verified`.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `chat`: narrowing and the not-found reply, the prompt-extraction refusal, the injection record and the Gold read budget.

## Impact

- `sentinel-ai-core/app/ai/grounding.py`, `app/orchestrator/step.py`, a guard module for the two pattern sets, `app/tools/bound.py`, locale files, tests and development cases.
- New adversarial run; README safety line, REQ-0021 evidence, `docs/build/security.md`, MT-06 retest.
- Not changed: the router, its prompt and labels, the policy engine, `eval-v7`, `2024Q4-resolution-v1`.

## Non-goals

- New intents (status, small talk) or model-extracted slots; `router-v3` covers openers.
- Blocking injected messages; the closed labels and the structured confirmation already stop the action.
- Approximate amounts.

## Assumptions

- This lands before `evaluation-final` and `router-v3` measure, so their runs see the final loop.
- Supersedes the changes `charge-narrowing`, `refuse-prompt-extraction` and `adversarial-gaps`.
