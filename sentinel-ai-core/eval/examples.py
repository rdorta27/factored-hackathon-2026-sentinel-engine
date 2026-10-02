"""Prompt examples for router version v2, drawn from the development split only.

Held-out cases never become examples (REQ-0017): building the block from a
held-out id fails before any model call.
"""

from __future__ import annotations

from app.ai.llm import Example
from eval.cases import Case

PROMPT_VERSION_WITH_EXAMPLES = "v2"


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


__all__ = ["PROMPT_VERSION_WITH_EXAMPLES", "HeldOutExample", "build_examples"]
