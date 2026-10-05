---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Attack coverage

**Choice:** the adversarial suite attempts every attack and counts the real outcome. The denominator is every attack attempted, so the rate cannot improve by shrinking the set.

**Why:** the brief asks for safety as the pass rate of what must not happen ([REQ-0021](../requirements/non-functional.md#req-0021)). A defence in code, a safe answer from the model and a known limitation must stay apart, or the rate is false.

**Evidence:** [`adversarial/20261005T014816Z`](../../evidence/adversarial/20261005T014816Z/summary.json), from `SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q`.

| Category | Attempted | Unsafe |
|---|---|---|
| A prompt injection | `categories.A_prompt_injection.attempted` 8 | 0/8 |
| B unauthorized access | `categories.B_unauthorized_access.attempted` 10 | 0/10 |
| C session | `categories.C_session.attempted` 6 | 0/6 |
| D tool failures | `categories.D_tool_failures.attempted` 6 | 0/6 |
| E multilingual ambiguity | `categories.E_multilingual_ambiguity.attempted` 6 | 0/6 |
| F decision disclosure | `categories.F_decision_disclosure.attempted` 6 | 0/6 |
| All | `totals.attempted` 42 | `totals.unsafe_outcome_rate` 0/42 |

The suite keeps four honesty groups apart: `blocked_verified` (38), `passes_on_mock` (3), `no_defense_yet` (0) and `documented` (1). The three mock-only attacks pass only because the live model is the keyword stand-in. The run [`adversarial/20261005T204313Z`](../../evidence/adversarial/20261005T204313Z/summary.json) repeats those three attacks against the real router model: `totals.unsafe_outcome_rate` 0/3.

The attack block of [`2024Q4-eval-v8`](../../evidence/evaluation-runs/2024Q4-eval-v8/summary.json) tests the model with 84 attack cases and scores each candidate.

**Alternatives rejected:** count a stand-in's good manners as a defence. It inflates the rate. Shrink the set to the passing cases. The denominator is fixed to every attempt.

**In production:** the suite runs in CI. The `no_defense_yet` group grows with the PII vault of decision 004. The category-B cases stay documented limits.

**On the slide:** "We attempt every attack and count it. Zero of 42 attacks produce an unsafe outcome, and we name the three that pass only because of the stand-in model."

Traces to [REQ-0021](../requirements/non-functional.md#req-0021).
