# Proposal

## Why

`evaluate` today is a status check. The loop does not pass country, date, or person-ask count, and there is no per-country file. Eligibility and escalation must live in code, with parameters in configuration, before a model can open a dispute (REQ-0007, REQ-0033, REQ-0048, REQ-0049). Decisions 005 and 008.

## What Changes

- Replace the status-only check with `evaluate(request) -> hit`: outcome plus a citable `rule_id`. First matching rule wins.
- Add synthetic country files for MX, CO, and AR under `config/policy/`. Same rule ids, different currency. No Brazil file: `pt-BR` is a reply language, not an account country.
- Recompute the 90-day window from an injected demo date. The Gold flag is a hint. Day 90 allows; day 91 cites `window.expired`.
- First request for a person offers help. A repeat hands off (`person.insist`). The count stays in conversation state, not in the engine.
- Leave fraud, high-amount, and staleness thresholds null and marked provisional (decisions 25, 26, 27). A null threshold does not fire. A charge whose currency is not the file currency does not fire `amount.high`.
- Re-run policy before `open_dispute`, including the confirmation turn. A hit other than allow rejects the write.
- Call the category port only after allow.

Person-offer, `person_asks`, and the window are already required by `decision-priority` and `orchestrator-loop`. This change implements them and adds the configuration contract.

## Capabilities

### New Capabilities

- `policy-engine`: pure rule evaluation, per-country files, provisional thresholds, and fail-closed unknown countries.

### Modified Capabilities

- None. Existing requirements already state the person-offer and window outcomes. This change does not alter those sentences.

## Impact

- `sentinel-ai-core/app/policy/` and `sentinel-ai-core/config/policy/`.
- `step` stops short-circuiting a person request and passes country, demo date, and `person_asks`.
- No HTTP route, no real model, no measured thresholds.

## Non-goals

- Choosing the numbers for decisions 25, 26, and 27.
- A Brazil account policy, or copying MX onto an unknown country.
- Repeat-customer handoff. Decision 003 names it; the charge has no such signal.
- Opening a dispute when the lookup is empty (pending verification). That stays a loop path, not a rule.
- Logging `policy_rule`. The hit already carries the id.
