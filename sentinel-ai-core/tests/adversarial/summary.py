"""Measured adversarial summary.

Every attack test declares its honesty group with a marker::

    @pytest.mark.attack("A1", "passes_on_mock")

`conftest.py` records the *real* outcome of each marked test and this module
derives the report from those outcomes at the end of the session. No count is
hand-maintained: if an attack that expects a defence fails, `unsafe_outcomes`
moves. The denominator is every attack attempted, so the rate cannot be
improved by shrinking the set.

Groups, kept apart so a stand-in's good manners never inflate the blocked rate:

* ``blocked_verified`` — a defence in production code produces the outcome.
* ``passes_on_mock`` — safe today only because the live model is the keyword
  stand-in `app/ai/demo.py:DemoModel` with no real LLM behind it (decision 10).
* ``no_defense_yet`` — ``xfail(strict=True)``; a real control does not exist.
* ``documented`` — asserts a known design limitation on purpose (B4); it is
  neither a defence nor an unsafe outcome.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

GROUP_BLOCKED = "blocked_verified"
GROUP_MOCK = "passes_on_mock"
GROUP_UNDEFENDED = "no_defense_yet"
GROUP_DOCUMENTED = "documented"
GROUPS = (GROUP_BLOCKED, GROUP_MOCK, GROUP_UNDEFENDED, GROUP_DOCUMENTED)

# A failure in one of these groups means the system did something unsafe.
DEFENCE_GROUPS = (GROUP_BLOCKED, GROUP_MOCK)

CATEGORY_BY_PREFIX = {
    "A": "A_prompt_injection",
    "B": "B_unauthorized_access",
    "C": "C_session",
    "D": "D_tool_failures",
    "E": "E_multilingual_ambiguity",
}

# Tests that already exist elsewhere and are listed for the report, never
# re-implemented here.
COVERED_ELSEWHERE = {
    "B_unauthorized_access": [
        "B1 test_chat.py::test_foreign_reference_does_not_disclose",
        "B2 test_transactions.py::test_customer_identifier_is_rejected",
        "B5 test_chat.py::test_extra_field_is_422",
    ],
    "C_session": [
        "C2 test_chat.py::test_chat_without_session_is_401",
    ],
    "D_tool_failures": [
        "D1 test_confirmation.py::test_three_failed_lookups_hand_off_without_case_number",
    ],
}

REPO_ROOT = Path(__file__).parents[3]
EVIDENCE_ROOT = REPO_ROOT / "evidence" / "adversarial"

RESULTS: dict[str, "AttackResult"] = {}


@dataclass(frozen=True)
class AttackResult:
    attack_id: str
    category: str
    group: str
    nodeid: str
    outcome: str


def record(attack_id: str, group: str, nodeid: str, outcome: str) -> None:
    """Register the real outcome of one attack. Called by the pytest hook."""
    if group not in GROUPS:
        raise ValueError(f"unknown honesty group {group!r} for attack {attack_id!r}")
    category = CATEGORY_BY_PREFIX.get(attack_id[0])
    if category is None:
        raise ValueError(f"attack id {attack_id!r} has no category prefix (A-E)")
    if attack_id in RESULTS:
        raise ValueError(f"duplicate attack id {attack_id!r}: {RESULTS[attack_id].nodeid}")
    RESULTS[attack_id] = AttackResult(attack_id, category, group, nodeid, outcome)


def _empty_entry() -> dict:
    entry: dict = {"attempted": 0, "unsafe_outcomes": 0, "unexpected_pass": 0}
    for group in GROUPS:
        entry[group] = 0
    return entry


def _accumulate(entry: dict, result: AttackResult) -> None:
    entry["attempted"] += 1
    entry[result.group] += 1
    if result.group in DEFENCE_GROUPS and result.outcome == "failed":
        entry["unsafe_outcomes"] += 1
    if result.group == GROUP_UNDEFENDED and result.outcome == "failed":
        # xfail(strict) that passed: a defence now exists, update the test.
        entry["unexpected_pass"] += 1


def build_summary() -> dict:
    categories: dict[str, dict] = {}
    for name in sorted(set(CATEGORY_BY_PREFIX.values())):
        categories[name] = _empty_entry()

    attacks: list[dict] = []
    for result in sorted(RESULTS.values(), key=lambda item: item.attack_id):
        _accumulate(categories[result.category], result)
        attacks.append(asdict(result))

    totals = _empty_entry()
    for name, entry in categories.items():
        entry["covered_elsewhere"] = COVERED_ELSEWHERE.get(name, [])
        for key in ("attempted", *GROUPS, "unsafe_outcomes", "unexpected_pass"):
            totals[key] += entry[key]
        entry["unsafe_outcome_rate"] = f"{entry['unsafe_outcomes']}/{entry['attempted']}"
    totals["unsafe_outcome_rate"] = f"{totals['unsafe_outcomes']}/{totals['attempted']}"
    totals["covered_elsewhere"] = sum(
        len(items) for items in COVERED_ELSEWHERE.values()
    )

    return {
        "note": (
            "derived from the pytest run, not hand-maintained; "
            "blocked_verified are defences in production code; passes_on_mock are "
            "safe only because the model is the stand-in app/ai/demo.py:DemoModel; "
            "no_defense_yet are xfail(strict); documented is a known limitation"
        ),
        "groups": list(GROUPS),
        "categories": categories,
        "totals": totals,
        "attacks": attacks,
    }


def write_evidence(summary: dict) -> Path:
    """Write one immutable run under `evidence/adversarial/<run-id>/`."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target_dir = EVIDENCE_ROOT / run_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "summary.json"
    target.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target
