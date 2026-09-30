# Proposal

## Why

The evaluation asks for measured failure handling on held-out attacks, reported
with denominators (REQ-0021). Today the coverage is scattered across test files
and has no spec-level contract, so nobody can say what is covered, what is only
safe because the model is a stand-in, or what has no control at all. Counting a
mock-only pass as a defence would overstate safety.

## What Changes

- New capability `failure-tests`: a contract that the system ships a measured
  adversarial set for bad or missing data, expired session, unauthorized
  access, prompt injection, tool failure and multilingual ambiguity, in
  `es-419` and `pt-BR`.
- Each attack is grouped by whether a real control exists: `blocked_verified`,
  `passes_on_mock`, `no_defense_yet` (`xfail(strict=True)`), or `documented`
  (a known limitation asserted on purpose).
- The report is derived from real pytest outcomes, never hand-maintained;
  `unsafe_outcome_rate` has every attempted attack as its denominator, so it
  cannot be improved by shrinking the set.
- Evidence is frozen write-once under `evidence/adversarial/<run-id>/`, written
  only when `SENTINEL_WRITE_EVIDENCE=1`.

## Capabilities

### New Capabilities

- `failure-tests`: measured adversarial coverage of REQ-0021 and REQ-0047, with
  honesty groups, a per-run derived summary and immutable evidence. Traces to
  REQ-0021, REQ-0047 and REQ-0007; see `docs/build/security.md`.

### Modified Capabilities

- None. The set verifies existing behavior (for example the inert-markup
  scenario in `chat-ui`); it does not change any requirement.

## Non-goals

Real-LLM hardening and system-prompt policy (decision 10); free-text PII
masking and the token vault (decision 004); a real HTTP client or tool timeout
(D4 stays `no_defense_yet`); any runtime behavior change. This change is tests,
evidence and their documentation only.

## Impact

New `sentinel-ai-core/tests/adversarial/` package (`conftest.py`, `summary.py`,
`test_a_injection.py` … `test_e_ambiguity.py`, `test_summary.py`, `README.md`);
a pytest `attack` marker in `sentinel-ai-core/pyproject.toml`; frozen evidence
in `evidence/adversarial/`; REQ-0021/REQ-0047 evidence in
`docs/requirements/requirements.md` and `team/tasks.md`; the evidence rule in
`AGENTS.md`. No production code changes.
