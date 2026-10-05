"""Prompt examples for router version v2, drawn from the development split only.

Held-out cases never become examples (REQ-0017): building the block from a
held-out id fails before any model call.
"""

from __future__ import annotations

from app.ai.llm import Example
from eval.cases import Case

PROMPT_VERSION_WITH_EXAMPLES = "v2"
PROMPT_VERSION_V3_WITH_EXAMPLES = "v3"


class HeldOutExample(ValueError):
    """An example id belongs to the held-out split."""


def build_examples(cases: list[Case], ids: list[str]) -> tuple[Example, ...]:
    by_id = {case.id: case for case in cases}
    examples = []
    for case_id in ids:
        case = by_id.get(case_id)
        if case is None:
            raise KeyError(f"example id {case_id!r} is not in the case set")
        if case.split != "development":
            raise HeldOutExample(f"example id {case_id!r} is in the {case.split} split")
        reply = {"intent": case.expected_intent, "language": case.locale, "amount": None, "not_mine": False}
        examples.append(Example(case_id=case.id, message=case.message, reply=reply))
    return tuple(examples)


def build_examples_v3(
    cases: list[Case], ids: list[str], drafts: dict[str, str] | None = None
) -> tuple[Example, ...]:
    """Prompt v3 examples: the v3 reply shape with kind, subtype and slots.

    ``drafts`` maps a case id to its example draft. Drafts teach when a draft
    is wanted: cases without one teach null.
    """
    by_id = {case.id: case for case in cases}
    examples = []
    for case_id in ids:
        case = by_id.get(case_id)
        if case is None:
            raise KeyError(f"example id {case_id!r} is not in the case set")
        if case.split != "development":
            raise HeldOutExample(f"example id {case_id!r} is in the {case.split} split")
        slots = dict(case.expected_slots) if case.expected_slots else {}
        reply = {
            "kind": case.expected_intent,
            "subtype": case.expected_subtype,
            "language": case.locale,
            "not_mine": False,
            "slots": {
                "merchant_words": slots.get("merchant_words"),
                "amount": slots.get("amount"),
                "date_phrase": slots.get("date_phrase"),
                "twice": slots.get("twice", False),
            },
            "reply_draft": (drafts or {}).get(case.id),
        }
        examples.append(Example(case_id=case.id, message=case.message, reply=reply))
    return tuple(examples)


__all__ = [
    "PROMPT_VERSION_WITH_EXAMPLES",
    "PROMPT_VERSION_V3_WITH_EXAMPLES",
    "HeldOutExample",
    "build_examples",
    "build_examples_v3",
]
