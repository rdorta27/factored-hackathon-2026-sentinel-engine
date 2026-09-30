# Design

## Context

See proposal.md. `app/policy/engine.py` takes only a charge status. `step` hands off a person request before calling it (`sentinel-ai-core/app/orchestrator/step.py`). Main specs already require the person-offer and the 90-day window. This change supplies the engine and the files.

## Goals / Non-Goals

**Goals:**

- A pure `evaluate` and three country files.
- The loop passes country, demo date, and `person_asks`.
- Tests cover one rule each, plus day 90/91 and the amount boundary.

**Non-Goals:**

- Measured thresholds. Null stays null.
- A loader that fetches Gold. The caller passes the candidate fields the engine needs.

## Decisions

### First match, escalate before status

Order: `person.insist`, configured fraud, configured high amount, status block, `window.expired`, `already.disputed`, `fields.missing`, `person.ask`, `allow`. A reversed charge does not hide an insist. Alternative rejected: the specification table order, which checks status first and swallows the handoff.

### Files hold parameters, code holds order

Each YAML file carries `synthetic: true`, country, currency, `demo_today`, `window_days`, status disputable flags, `rule_id`s, explanation texts keyed by `es-419` and `pt-BR`, mandatory fields, and provisional thresholds. The engine does not branch on `MX`. Unknown country fails closed. Alternative rejected: one shared file plus a currency map. A new country would then be a code edit.

### Demo date is injected

`PolicyRequest.today` is the demo clock. Tests set it. The file default is `2026-06-17`, the dataset end, and is not `date.today()`. A Q4-2024 charge is outside 90 days on that default. Callers that need an in-window charge pass an earlier date. Alternative rejected: using the dataset end as a silent "today" for every fixture.

### Candidate gains the signals the rules read

`fraud_score`, `is_disputed`, and the Gold eligibility hint are optional fields on the candidate. Missing `fraud_score` does not fire fraud. Currency mismatch skips `amount.high`. No FX. Alternative rejected: reading Gold inside `evaluate`.

### Hit is the only output

`PolicyHit` is outcome, `rule_id`, and `provisional`. The loop looks up explanation text by reply language. The engine does not draft the sentence.

## Risks / Trade-offs

- [Risk] Main specs already describe person-offer and the window, while the code does not → Mitigation: tasks wire `step` to the new hit before the change is done.
- [Risk] Provisional nulls look like missing config → Mitigation: each entry has `provisional: true` and the decision number. The hit says so when a value is later filled in.
- [Risk] Day-90 tests depend on the injected date → Mitigation: tests pass `today` and do not read the file default.

## Migration Plan

1. Add the engine and files. Keep the old `evaluate(PolicyFacts)` only until `step` calls the new function, then remove it.
2. Rollback is reverting this branch. No route depends on it.

## Open Questions

- None that change the task split. Repeat-customer handoff stays out until a signal exists.
