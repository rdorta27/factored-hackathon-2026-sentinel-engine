"""Versioned labelled case set for the evaluation harness.

Cases are team-written and declared simulation, never dataset rows.
One JSONL schema serves both drivers: the component benchmark reads the
intent labels, the system runner reads the outcome labels.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.port import SUBTYPE_MISSING, SUBTYPE_OUT_OF_SCOPE

LOCALES = ("es-419", "pt-BR")
COUNTRIES = ("MX", "CO", "AR")
INTENTS = ("charge", "status", "missing", "out_of_scope", "person")
SUBTYPES = tuple(sorted(SUBTYPE_MISSING | SUBTYPE_OUT_OF_SCOPE))
SLOT_KEYS = ("merchant_words", "amount", "date_phrase", "twice")
SPLITS = ("development", "validation", "held_out")
FAULTS = ("none", "gold_unavailable", "expired_session", "tool_failure")
KNOWN_TAGS = ("edge", "adversarial", "noisy")
# A variant is the language a base situation is rendered in, tied to the
# account country (decision 017: a pt-BR writer holds an MX, CO or AR account).
VARIANTS = {"es-MX": ("es-419", "MX"), "es-CO": ("es-419", "CO"), "es-AR": ("es-419", "AR"), "pt-BR": ("pt-BR", None)}
PERTURBATIONS = ("date_shift", "amount_shift", "truncated_name", "self_correction")

REQUIRED = (
    "id",
    "locale",
    "country",
    "turns",
    "expected_intent",
    "expected_outcome",
    "split",
)


@dataclass(frozen=True)
class Case:
    id: str
    locale: str
    country: str
    turns: tuple[str, ...]
    expected_intent: str
    expected_category: str | None
    expected_outcome: str
    requires_handoff: bool
    tags: tuple[str, ...] = ()
    split: str = "development"
    fault: str = "none"
    must_not_pass: bool = False
    # Optional second turn: the customer picks this charge, so policy rules on the
    # charge (amount, fraud score, claim) can fire. Then expected_rule names the rule.
    selected_reference: str | None = None
    expected_rule: str | None = None
    # Optional third turn: when the selection answers with a confirm box, send the
    # same charge again so the case reaches a verified case number. The harness
    # never confirms a case that does not ask for it.
    confirm: bool = False
    # Sealed-set fields: the base situation, its rendering, and for noisy twins
    # the single declared perturbation.
    base_id: str | None = None
    variant: str | None = None
    perturbation: str | None = None
    # Contract v3 labels: the subtype and the slot hints. Both stay None on
    # the v7 cases, so the old harness reads them unchanged.
    expected_subtype: str | None = None
    expected_slots: dict | None = None

    @property
    def message(self) -> str:
        return self.turns[0] if self.turns else ""


def validate_case(body: dict, source: str) -> Case:
    case_id = str(body.get("id") or source)
    for key in REQUIRED:
        if not body.get(key):
            raise ValueError(f"case {case_id} is missing label {key!r} ({source})")
    if body["locale"] not in LOCALES:
        raise ValueError(f"case {case_id} has unknown locale {body['locale']!r}")
    if body["country"] not in COUNTRIES:
        raise ValueError(f"case {case_id} has unknown country {body['country']!r}")
    if body["expected_intent"] not in INTENTS:
        raise ValueError(f"case {case_id} has unknown intent {body['expected_intent']!r}")
    if body["split"] not in SPLITS:
        raise ValueError(f"case {case_id} has unknown split {body['split']!r}")
    fault = body.get("fault", "none") or "none"
    if fault not in FAULTS:
        raise ValueError(f"case {case_id} has unknown fault {fault!r}")
    tags = tuple(body.get("tags", []) or [])
    for tag in tags:
        if tag not in KNOWN_TAGS:
            raise ValueError(f"case {case_id} has unknown tag {tag!r}")
    variant = body.get("variant") or None
    base_id = body.get("base_id") or None
    perturbation = body.get("perturbation") or None
    if variant is not None:
        if variant not in VARIANTS:
            raise ValueError(f"case {case_id} has unknown variant {variant!r}")
        locale, country = VARIANTS[variant]
        if body["locale"] != locale or (country is not None and body["country"] != country):
            raise ValueError(
                f"case {case_id} has variant {variant} but locale {body['locale']} and country {body['country']}"
            )
        if base_id is None:
            raise ValueError(f"case {case_id} has a variant but no base_id")
    if "noisy" in tags:
        if perturbation not in PERTURBATIONS:
            raise ValueError(f"noisy case {case_id} must name one perturbation of {PERTURBATIONS}")
        if base_id is None or variant is None:
            raise ValueError(f"noisy case {case_id} must reference its base_id and variant")
    elif perturbation is not None:
        raise ValueError(f"case {case_id} names a perturbation but is not tagged noisy")
    turns = body["turns"]
    if not isinstance(turns, list) or not all(isinstance(t, str) and t.strip() for t in turns):
        raise ValueError(f"case {case_id} needs non-empty string turns")
    subtype = body.get("expected_subtype") or None
    if subtype is not None:
        if subtype not in SUBTYPES:
            raise ValueError(f"case {case_id} has unknown subtype {subtype!r}")
        if body["expected_intent"] == "missing" and subtype not in SUBTYPE_MISSING:
            raise ValueError(f"case {case_id} pairs intent missing with subtype {subtype!r}")
        if body["expected_intent"] == "out_of_scope" and subtype not in SUBTYPE_OUT_OF_SCOPE:
            raise ValueError(f"case {case_id} pairs intent out_of_scope with subtype {subtype!r}")
        if body["expected_intent"] not in ("missing", "out_of_scope"):
            raise ValueError(f"case {case_id} pairs intent {body['expected_intent']!r} with a subtype")
    slots = body.get("expected_slots") or None
    if slots is not None:
        if not isinstance(slots, dict):
            raise ValueError(f"case {case_id} needs expected_slots as an object")
        for key in slots:
            if key not in SLOT_KEYS:
                raise ValueError(f"case {case_id} has unknown slot {key!r}")
        merchant_words = slots.get("merchant_words")
        if merchant_words is not None and not (isinstance(merchant_words, str) and merchant_words.strip()):
            raise ValueError(f"case {case_id} needs merchant_words as a non-empty string")
        amount = slots.get("amount")
        if amount is not None and (isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0):
            raise ValueError(f"case {case_id} needs amount as a non-negative number")
        date_phrase = slots.get("date_phrase")
        if date_phrase is not None and not (isinstance(date_phrase, str) and date_phrase.strip()):
            raise ValueError(f"case {case_id} needs date_phrase as a non-empty string")
        if "twice" in slots and not isinstance(slots["twice"], bool):
            raise ValueError(f"case {case_id} needs twice as a boolean")
    return Case(
        id=str(body["id"]),
        locale=str(body["locale"]),
        country=str(body["country"]),
        turns=tuple(turns),
        expected_intent=str(body["expected_intent"]),
        expected_category=body.get("expected_category"),
        expected_outcome=str(body["expected_outcome"]),
        requires_handoff=bool(body.get("requires_handoff", False)),
        tags=tags,
        split=str(body["split"]),
        fault=fault,
        must_not_pass=bool(body.get("must_not_pass", False)),
        selected_reference=body.get("selected_reference") or None,
        expected_rule=body.get("expected_rule") or None,
        confirm=bool(body.get("confirm", False)),
        base_id=base_id,
        variant=variant,
        perturbation=perturbation,
        expected_subtype=subtype,
        expected_slots=dict(slots) if slots is not None else None,
    )


def load_cases(path: Path | str) -> list[Case]:
    path = Path(path)
    cases = []
    with path.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            cases.append(validate_case(json.loads(line), f"{path}:{lineno}"))
    return cases


# The resolution set lives beside the development set but is not part of it: it
# is loaded explicitly by the resolution run, never by ``load_dir``.
RESOLUTION_FILE = "resolution.jsonl"


def load_dir(directory: Path | str, exclude: tuple[str, ...] = (RESOLUTION_FILE,)) -> list[Case]:
    cases = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        if path.name in exclude:
            continue
        cases.extend(load_cases(path))
    return cases


def base_of(case: Case) -> str:
    """The base situation: its ``base_id``, or the case id when it has none."""
    return case.base_id or case.id


def check_splits(cases: list[Case]) -> None:
    """No case id and no base may appear in more than one split.

    The validation split is carved from development by base (018 amendment), so
    a base that straddles two splits would leak between them.
    """
    seen_ids: dict[str, str] = {}
    seen_bases: dict[str, str] = {}
    for case in cases:
        prior = seen_ids.get(case.id)
        if prior is not None and prior != case.split:
            raise ValueError(f"case id {case.id} appears in both {prior} and {case.split} splits")
        seen_ids[case.id] = case.split
        base = base_of(case)
        prior = seen_bases.get(base)
        if prior is not None and prior != case.split:
            raise ValueError(f"base {base} appears in both {prior} and {case.split} splits")
        seen_bases[base] = case.split


@dataclass(frozen=True)
class LabelProvenance:
    run_id: str
    summary_sha16: str
    claim_labels: tuple[str, ...] = field(default=())


def load_labels(path: Path | str) -> LabelProvenance:
    body = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("run_id", "summary_sha16"):
        if not body.get(key):
            raise ValueError(f"labels file {path} is missing {key!r}")
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return LabelProvenance(
        run_id=str(body["run_id"]),
        summary_sha16=str(body["summary_sha16"]),
        claim_labels=tuple(body.get("claim_labels", [])),
    )


__all__ = [
    "COUNTRIES",
    "FAULTS",
    "INTENTS",
    "LOCALES",
    "PERTURBATIONS",
    "RESOLUTION_FILE",
    "SLOT_KEYS",
    "SPLITS",
    "SUBTYPES",
    "VARIANTS",
    "Case",
    "LabelProvenance",
    "base_of",
    "check_splits",
    "load_cases",
    "load_dir",
    "load_labels",
    "validate_case",
]
