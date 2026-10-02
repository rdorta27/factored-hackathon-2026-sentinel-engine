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

LOCALES = ("es-419", "pt-BR")
COUNTRIES = ("MX", "CO", "AR")
INTENTS = ("charge", "missing", "out_of_scope", "person")
SPLITS = ("development", "held_out")
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
    # Sealed-set fields: the base situation, its rendering, and for noisy twins
    # the single declared perturbation.
    base_id: str | None = None
    variant: str | None = None
    perturbation: str | None = None

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
        base_id=base_id,
        variant=variant,
        perturbation=perturbation,
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


def load_dir(directory: Path | str) -> list[Case]:
    cases = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        cases.extend(load_cases(path))
    return cases


def check_splits(cases: list[Case]) -> None:
    dev = {c.id for c in cases if c.split == "development"}
    held = {c.id for c in cases if c.split == "held_out"}
    overlap = dev & held
    if overlap:
        raise ValueError(f"case ids appear in both splits: {sorted(overlap)}")


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
    "SPLITS",
    "VARIANTS",
    "Case",
    "LabelProvenance",
    "check_splits",
    "load_cases",
    "load_dir",
    "load_labels",
    "validate_case",
]
