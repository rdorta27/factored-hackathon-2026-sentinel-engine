# Proposal

## Why

The router returns only a label (`charge`, `missing`, `out_of_scope`, `person`), the language and the not-mine claim (`UnderstandResult`, `app/ai/port.py`); it gives no measure of how sure it is. Every label is treated the same, so a doubtful `charge` goes straight to the charge path. A confidence score with fitted cut-offs would let the loop act when the label is clear, ask a clarifying question when it is borderline, and abstain when it is not, with the cut-offs chosen from data rather than from the prompt. The brief asks to clarify ambiguity, know when not to act, and justify thresholds and splits (REQ-0002, REQ-0006, REQ-0016, REQ-0017).

## What Changes

- **Feasibility first:** check that the provider returns token log-probabilities for the served model (GLM 5.3 Flash on Fireworks) with JSON output and low reasoning. If it does not, the change stops, the result is documented, and nothing else is built.
- **Score:** the router derives a confidence for its label from the log-probabilities of the label token, recorded on the `understand` record with the label.
- **Validation split:** a new split carved from development by base, so cut-offs are fitted on development, chosen on validation and reported on the sealed held-out set of `eval-v8`.
- **Two cut-offs:** `t_act` (at or above: the label is used) and `t_abstain` (below: the turn asks for clarification, or offers an advisor after the existing clarification limit); between them the turn asks for clarification. They live in the router configuration with their source run, never in the country policy files.
- **Policy still decides:** a confident label cannot override a policy refusal, a handoff rule or the confirm box.
- **Behind a setting:** served only when the setting is on and the `eval-v8` measurement passes the 018 amendment; otherwise v2 without cut-offs stays served.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `llm-router`: a confidence per label and cut-offs that map it to act, clarify or abstain.
- `evaluation-runner`: a validation split and a calibration report.

## Impact

- `sentinel-ai-core/app/ai/` (transport request, router, serving), `app/orchestrator/step.py` (clarify on a borderline label), `eval/` (split, calibration run), a router configuration file with the cut-offs, tests.
- Not changed: the policy engine and its files, the label set, the reply contract.

## Non-goals

- Model-decided actions or eligibility.
- Thresholds per country or currency.
- A new model.

## Assumptions

- Lands before the `eval-v8` seal so one sealed measurement covers it (`router-v3`).
- If the feasibility check fails, `router-v3` measures v3 without cut-offs.
