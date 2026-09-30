# Design

## Context

The adversarial tests already exist as plain pytest modules. The problem is
that the summary was a hand-written table, so `unsafe_outcomes` was always
zero and three attacks passed for the wrong reason. See `proposal.md` — Why.

Constraints: Python 3.12 + pytest; no new dependency; the report must be
reproducible and the evidence write-once (`AGENTS.md`); the suite must stay
fast and must not write to the repo on a normal run.

## Goals / Non-Goals

**Goals:**

- Derive the report from the real pytest outcomes, so a failing defence attack
  moves `unsafe_outcomes`.
- Keep the honesty groups visible on each test.
- Freeze one evidence run per opt-in invocation without overwriting earlier
  runs.

**Non-Goals:**

- Parsing coverage or mutating production code.
- Real model hardening, PII masking, or tool timeouts (decision 10,
  decision 004).

## Decisions

- **Markers plus pytest hooks, not a static table.** Each attack carries
  `@pytest.mark.attack(id, group)`; `conftest.py` records the call-phase report
  and `summary.py` derives the report. Alternative: a separate runner parsing
  `--junitxml`. Rejected because it adds a second execution path and a file the
  tests must trust; hooks read the run the suite already produces.
- **`pytest_runtest_makereport` (hookwrapper) over `pytest_runtest_logreport`.**
  Only the item-based report exposes the marker args, so the attack id and group
  travel with the outcome.
- **Collection fails on an unmarked attack.** A new test that forgets the marker
  would silently drop from the denominator; failing collection keeps the
  denominator honest.
- **`no_defense_yet` stays `xfail(strict=True)`.** An unexpected pass fails the
  suite and forces reclassification instead of quietly inflating the blocked
  rate.
- **Evidence under `evidence/adversarial/<run-id>/`, opt-in via
  `SENTINEL_WRITE_EVIDENCE=1`.** A new timestamped folder per run satisfies the
  write-once rule; a normal run writes nothing.

## Risks / Trade-offs

- [Ordering: the summary check needs every attack recorded] → the collection
  hook moves `test_summary.py` to the end of the run.
- [A `no_defense_yet` test that sleeps would slow the suite] → the D4 delay is
  kept small and the test documents that a real timeout is the unblocker.
- [The report could still be read as a safety score] → `passes_on_mock` is kept
  out of `blocked_verified` and the rate is always shown with its denominator.
