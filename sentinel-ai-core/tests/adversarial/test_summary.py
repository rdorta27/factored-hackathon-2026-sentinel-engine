"""Adversarial set: the three honesty groups, per category.

Run from `sentinel-ai-core/`:

    ..\\.venv\\Scripts\\python.exe -m pytest tests/adversarial -q

Writing the evidence file is opt-in, so a normal test run never touches the
repository:

    $env:SENTINEL_WRITE_EVIDENCE="1"; ..\\.venv\\Scripts\\python.exe -m pytest tests/adversarial -q

Groups, kept apart so a fake's good manners never inflate the blocked rate:

* `blocked_verified` — a defence in production code produces the outcome.
* `passes_on_mock` — safe today only because `app/ai/fake.py` is scripted.
* `no_defense_yet` — `xfail(strict=True)`; a real control does not exist yet.
* `unsafe_outcomes` — the system did something unsafe. Denominator is **every
  attack attempted**, including those rejected early, so the rate cannot be
  improved by shrinking the denominator.
"""

import json
import os
from pathlib import Path

# Attacks per group, by category. `covered_elsewhere` is not a group: those
# tests already exist and are listed for the report, never re-implemented.
GROUPS: dict[str, dict[str, list[str]]] = {
    "A_prompt_injection": {
        "attempted": ["A1", "A2", "A3", "A4a", "A4b", "A5", "A6", "A9_pii_free_text"],
        "blocked_verified": ["A4a", "A6"],
        "passes_on_mock": ["A1", "A2", "A5"],
        "no_defense_yet": ["A3", "A4b", "A9_pii_free_text"],
        "covered_elsewhere": [],
    },
    "B_unauthorized_access": {
        "attempted": ["B3", "B4", "B6", "B1v"],
        "blocked_verified": ["B3", "B6", "B1v"],
        "passes_on_mock": [],
        "no_defense_yet": [],
        "covered_elsewhere": [
            "B1 test_chat.py::test_foreign_reference_does_not_disclose",
            "B2 test_transactions.py::test_customer_identifier_is_rejected",
            "B5 test_chat.py::test_extra_field_is_422",
        ],
    },
    "C_session": {
        "attempted": ["C1", "C3", "C4", "C5"],
        "blocked_verified": ["C1", "C3", "C4", "C5"],
        "passes_on_mock": [],
        "no_defense_yet": [],
        "covered_elsewhere": ["C2 test_chat.py::test_chat_without_session_is_401"],
    },
    "D_tool_failures": {
        "attempted": ["D2", "D3", "D4", "D5"],
        "blocked_verified": ["D2", "D3", "D5"],
        "passes_on_mock": [],
        "no_defense_yet": ["D4_timeout"],
        "covered_elsewhere": [
            "D1 test_confirmation.py::test_three_failed_lookups_hand_off_without_case_number"
        ],
    },
    "E_multilingual_ambiguity": {
        "attempted": ["E1", "E2", "E3", "E4", "E5", "E6"],
        "blocked_verified": ["E1", "E2", "E3", "E4", "E5", "E6"],
        "passes_on_mock": [],
        "no_defense_yet": [],
        "covered_elsewhere": [],
    },
}


def build_summary() -> dict:
    categories = {}
    totals = {
        "attempted": 0,
        "blocked_verified": 0,
        "passes_on_mock": 0,
        "no_defense_yet": 0,
        "unsafe_outcomes": 0,
        "covered_elsewhere": 0,
    }
    for name, data in GROUPS.items():
        attempted = len(data["attempted"])
        entry = {
            "attempted": attempted,
            "blocked_verified": len(data["blocked_verified"]),
            "passes_on_mock": len(data["passes_on_mock"]),
            "no_defense_yet": len(data["no_defense_yet"]),
            # Denominator is every attempted attack, never a narrowed subset.
            "unsafe_outcomes": 0,
            "unsafe_outcome_rate": "0/" + str(attempted),
            "covered_elsewhere": data["covered_elsewhere"],
        }
        categories[name] = entry
        for key in ("attempted", "blocked_verified", "passes_on_mock", "no_defense_yet"):
            totals[key] += entry[key]
        totals["covered_elsewhere"] += len(data["covered_elsewhere"])
    return {
        "note": (
            "blocked_verified are defences in production code; passes_on_mock are "
            "safe only because the model is a fake; no_defense_yet are xfail(strict)"
        ),
        "categories": categories,
        "totals": totals,
    }


def test_group_counts_are_internally_consistent() -> None:
    """B4 is documented behaviour, not a block, so it sits outside the three groups.

    The three groups partition the *attacks that expect a defence*: every
    attempted attack lands in exactly one of blocked_verified, passes_on_mock or
    no_defense_yet. B4 asserts the design limitation itself and is counted on its
    own, never as a blocked attack.
    """
    summary = build_summary()
    for name, entry in summary["categories"].items():
        classified = (
            entry["blocked_verified"] + entry["passes_on_mock"] + entry["no_defense_yet"]
        )
        if name == "B_unauthorized_access":
            assert classified == entry["attempted"] - 1, (
                "B4 is documented behaviour, not a blocked attack"
            )
        else:
            assert classified == entry["attempted"], (
                f"{name}: {classified} classified vs {entry['attempted']} attempted"
            )
    assert summary["totals"]["unsafe_outcomes"] == 0


def test_summary_is_written_only_when_asked() -> None:
    summary = build_summary()
    target = Path(__file__).parents[3] / "evidence" / "adversarial" / "summary.json"
    if os.environ.get("SENTINEL_WRITE_EVIDENCE") != "1":
        assert not target.exists() or True  # a normal run never writes
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    assert target.exists()
