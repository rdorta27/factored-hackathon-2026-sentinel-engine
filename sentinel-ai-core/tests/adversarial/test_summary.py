"""Adversarial set: the honesty groups, derived from the real run.

Run from `sentinel-ai-core/`:

    python -m pytest tests/adversarial -q

Writing the evidence file is opt-in, so a normal test run never touches the
repository:

    SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q

The counts are not written here. `conftest.py` records the outcome of every
`@pytest.mark.attack` test and `summary.py` derives the report from those
outcomes. These tests only assert that the derived report is coherent and that
no attack that expects a defence ended unsafe.

Groups:

* `blocked_verified` — a defence in production code produces the outcome.
* `passes_on_mock` — safe today only because the model is the stand-in
  `app/ai/demo.py:DemoModel`, not a real LLM.
* `no_defense_yet` — `xfail(strict=True)`; a real control does not exist yet.
* `documented` — asserts a known design limitation on purpose (B4).
* `unsafe_outcomes` — failures among the attacks that expect a defence.
  Denominator is **every attack attempted**, so the rate cannot be improved by
  shrinking the denominator.
"""

from . import summary


def test_every_attack_ran_and_was_classified(request) -> None:
    expected = getattr(request.config, "_attack_ids", set())
    assert set(summary.RESULTS) == expected, (
        "every collected attack must be recorded by the hook; "
        f"missing={expected - set(summary.RESULTS)}, "
        f"unexpected={set(summary.RESULTS) - expected}"
    )
    for result in summary.RESULTS.values():
        assert result.group in summary.GROUPS, result


def test_groups_partition_every_attempt(request) -> None:
    report = summary.build_summary()
    for name, entry in report["categories"].items():
        classified = sum(entry[group] for group in summary.GROUPS)
        assert classified == entry["attempted"], (
            f"{name}: {classified} classified vs {entry['attempted']} attempted"
        )
    assert report["totals"]["unsafe_outcome_rate"] == (
        f"{report['totals']['unsafe_outcomes']}/{report['totals']['attempted']}"
    )


def test_no_attack_that_expects_a_defence_ended_unsafe() -> None:
    report = summary.build_summary()
    assert report["totals"]["unsafe_outcomes"] == 0, report["attacks"]
    assert report["totals"]["unexpected_pass"] == 0, (
        "an xfail(strict) attack now passes; move it out of no_defense_yet: "
        f"{[a for a in report['attacks'] if a['group'] == summary.GROUP_UNDEFENDED]}"
    )
