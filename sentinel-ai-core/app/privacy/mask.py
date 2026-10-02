"""Mask free-text customer messages before they reach the model (REQ-0047).

One call, ``mask(text)``, returns the same sentence with every detected
identifier replaced by a typed marker. Irreversible by design: the demo has no
tool that needs the original value, so no token vault is built (decision 004).

Precedence, in order:

1. Typed identifiers with a check digit (card, CURP, CLABE, CPF, CUIT, RFC).
2. Email.
3. Bare-number identifiers (cedula, DNI, phone) **only** near a trigger word.
4. Names the customer introduces ("me llamo Karl", "soy Karl", "meu nome é Karl").
5. Everything else is left untouched, including amounts and dates.

A trigger word beats amount protection on purpose: "mi DNI es 12.345.678" is a
document even though it is shaped like an amount, because the customer said so.
"""

import re

from app.privacy.detectors import (
    BARE_ID,
    CARD,
    CLABE,
    CPF,
    CUIT,
    CURP,
    DOCUMENT_NUMBER,
    EMAIL,
    PHONE,
    RFC,
    Finding,
    clabe_ok,
    cpf_ok,
    cuit_ok,
    curp_ok,
    has_contact_trigger,
    has_document_trigger,
    has_trigger,
    luhn_ok,
    name_findings,
)

MARKERS = {
    "card": "[CARD]",
    "curp": "[CURP]",
    "rfc": "[RFC]",
    "clabe": "[CLABE]",
    "cpf": "[CPF]",
    "cuit": "[CUIT]",
    "document": "[DOC_ID]",
    "phone": "[PHONE]",
    "email": "[EMAIL]",
    "name": "[NAME]",
}

# Amounts and dates the grounding depends on. They are never masked unless a
# trigger word claims the value (see the module docstring).
AMOUNT = re.compile(r"(?:r\$\s*)?\$?\s?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{2})?")
DATE_ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
DATE_SLASH = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b")


def _protected_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    for pattern in (DATE_ISO, DATE_SLASH, AMOUNT):
        spans.extend(match.span() for match in pattern.finditer(text))
    return spans


def _overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    return any(start < span[1] and span[0] < end for start, end in spans)


def _find(text: str) -> list[Finding]:
    """All findings, most specific first, without overlapping duplicates."""
    findings: list[Finding] = []

    def add(kind: str, match: re.Match[str], validator=None) -> None:  # type: ignore[no-untyped-def]
        value = match.group(0)
        if validator is not None and not validator(value):
            return
        findings.append(Finding(kind, match.start(), match.end(), value))

    # 1. Typed identifiers, each guarded by its checksum.
    for match in CURP.finditer(text):
        add("curp", match, curp_ok)
    for match in CLABE.finditer(text):
        add("clabe", match, clabe_ok)
    for match in CPF.finditer(text):
        add("cpf", match, cpf_ok)
    for match in CUIT.finditer(text):
        add("cuit", match, cuit_ok)
    for match in CARD.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if luhn_ok(digits):
            findings.append(Finding("card", match.start(), match.end(), match.group(0)))
    for match in RFC.finditer(text):
        # RFC shares a shape with card fragments; only accept it when a trigger
        # names it, to avoid masking merchant codes.
        if has_trigger(text, match.start(), match.end()):
            add("rfc", match)

    # 2. Email.
    for match in EMAIL.finditer(text):
        add("email", match)

    # 3. Bare-number identifiers: only with a trigger, and documents before
    #    contacts, so a cedula is never mislabelled as a phone.
    taken = [(f.start, f.end) for f in findings]

    def record(kind: str, match: re.Match[str]) -> None:  # type: ignore[no-untyped-def]
        if any(s < match.end() and match.start() < e for s, e in taken):
            return
        findings.append(Finding(kind, match.start(), match.end(), match.group(0)))
        taken.append((match.start(), match.end()))

    for match in DOCUMENT_NUMBER.finditer(text):
        if has_document_trigger(text, match.start(), match.end()):
            record("document", match)

    for match in BARE_ID.finditer(text):
        if has_trigger(text, match.start(), match.end()):
            record("document", match)

    for match in PHONE.finditer(text):
        if not has_contact_trigger(text, match.start(), match.end()):
            continue
        if len(re.sub(r"\D", "", match.group(0))) >= 9:
            record("phone", match)

    # 4. Names the customer introduces ("me llamo Karl"); never guessed.
    for finding in name_findings(text):
        if not any(s < finding.end and finding.start < e for s, e in taken):
            findings.append(finding)

    return findings


def mask(text: str) -> str:
    """Replace every detected identifier with its typed marker."""
    if not text:
        return text
    findings = sorted(_find(text), key=lambda f: f.start, reverse=True)
    masked = text
    for finding in findings:
        masked = masked[:finding.start] + MARKERS[finding.kind] + masked[finding.end:]
    return masked


def contains_identifier(text: str) -> bool:
    """True when the text has at least one detected identifier."""
    return bool(_find(text))
