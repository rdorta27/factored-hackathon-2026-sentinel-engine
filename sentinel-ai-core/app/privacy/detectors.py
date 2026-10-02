"""Typed PII detectors with validators.

Design rules that keep the grounding intact:

* **Validators are mandatory where a check digit exists.** A card must pass
  Luhn, a CURP/CLABE/CUIT/CPF must pass its own checksum. Without this, any long
  number a customer types (a large amount, a reference) would be masked and the
  grounding would stop recognising the charge.
* **Trigger words are mandatory for bare-number identifiers.** A Colombian
  cedula, an Argentine DNI and a phone number are just digit strings; matching
  them unconditionally would swallow amounts. They only match near a trigger.
* **A trigger wins over amount protection.** "mi DNI es 12.345.678" must mask
  even though the number looks like an amount, because the customer said what it
  is. Amount protection applies only when no trigger is present.

Irreversible typed markers, per the approved plan: there is no token vault,
because no tool needs the original value (decision 004: the session identifies
the customer).
"""

import re
from dataclasses import dataclass

# --- validators -----------------------------------------------------------


def luhn_ok(digits: str) -> bool:
    """Luhn check for card numbers."""
    if not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def clabe_ok(digits: str) -> bool:
    """CLABE: 18 digits, weighted mod-10 check digit."""
    if len(digits) != 18 or not digits.isdigit():
        return False
    weights = [3, 7, 1] * 6
    total = sum((int(d) * w) % 10 for d, w in zip(digits[:17], weights))
    return (10 - total % 10) % 10 == int(digits[17])


def curp_ok(value: str) -> bool:
    """CURP: shape plus the official mod-10 check digit."""
    if not re.fullmatch(r"[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d", value):
        return False
    alphabet = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
    total = sum(alphabet.index(c) * (18 - i) for i, c in enumerate(value[:17]))
    return (10 - total % 10) % 10 == int(value[17])


def cuit_ok(value: str) -> bool:
    """CUIT/CUIL: 11 digits with mod-11 check digit."""
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        return False
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(digits, weights))
    check = 11 - total % 11
    if check == 11:
        check = 0
    elif check == 10:
        check = 9
    return check == int(digits[10])


def cpf_ok(value: str) -> bool:
    """CPF: 11 digits with the two mod-11 check digits."""
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    for length in (9, 10):
        total = sum(int(d) * (length + 1 - i) for i, d in enumerate(digits[:length]))
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if check != int(digits[length]):
            return False
    return True


# --- patterns -------------------------------------------------------------

TRIGGERS = (
    "dni", "cédula", "cedula", "documento", "identificación", "identificacion",
    "curp", "rfc", "cpf", "cuit", "cuil", "clabe", "pasaporte",
    "teléfono", "telefono", "celular", "whatsapp", "llamar", "marcar",
    "correo", "email", "e-mail",
)

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")
CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
CURP = re.compile(r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d\b")
RFC = re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b")
CLABE = re.compile(r"\b\d{18}\b")
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CUIT = re.compile(r"\b\d{2}-?\d{8}-?\d\b")
BARE_ID = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}\b")  # 7-8 digits, optional dots
# A bare digit run with a document trigger: cedula (CO), DNI (AR), passport.
DOCUMENT_NUMBER = re.compile(r"\b\d{6,12}\b")
PHONE = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}\b")

DOCUMENT_TRIGGERS = (
    "dni", "cédula", "cedula", "documento", "identificación", "identificacion",
    "pasaporte", "cuit", "cuil", "cpf", "curp", "rfc",
)
CONTACT_TRIGGERS = ("teléfono", "telefono", "celular", "whatsapp", "llamar", "marcar")


@dataclass(frozen=True)
class Finding:
    """One detected identifier: its kind, the span, and the matched text."""

    kind: str
    start: int
    end: int
    text: str


def has_trigger(text: str, start: int, end: int, window: int = 40) -> bool:
    """True when any trigger word sits near the candidate value."""
    lowered = text.lower()
    before = lowered[max(0, start - window):start]
    after = lowered[end:end + window]
    return any(trigger in before or trigger in after for trigger in TRIGGERS)


def has_document_trigger(text: str, start: int, end: int, window: int = 40) -> bool:
    lowered = text.lower()
    before = lowered[max(0, start - window):start]
    after = lowered[end:end + window]
    return any(t in before or t in after for t in DOCUMENT_TRIGGERS)


def has_contact_trigger(text: str, start: int, end: int, window: int = 40) -> bool:
    lowered = text.lower()
    before = lowered[max(0, start - window):start]
    after = lowered[end:end + window]
    return any(t in before or t in after for t in CONTACT_TRIGGERS)


# --- self-introduced names -------------------------------------------------
#
# A name is only masked when the customer introduces it ("me llamo Karl"). There
# is no name list: no trigger, no mask. The strong triggers name the person
# outright, so the words after them are masked in any case; "soy"/"sou" also
# introduce roles ("soy cliente"), so the weak ones need a capitalised word.

_WORD = r"[^\W\d_]+(?:['\-][^\W\d_]+)*"
_NAME_STOP = frozenset(
    "y e and pero mas mais que porque porq ya hoy tengo tenho quiero quero necesito preciso "
    "no nao não con com para por en em de del da do la el los las un una uma".split()
)
_PARTICLES = frozenset("de del da do dos das la".split())
_ROLE_WORDS = frozenset(
    "cliente titular usuario usuaria correntista yo eu nuevo nueva novo nova".split()
)

STRONG_NAME_INTRO = re.compile(
    r"(?i:\b(?:me\s+llamo|mi\s+nombre\s+(?:completo\s+)?es|meu\s+nome\s+(?:completo\s+)?[eé]|"
    r"me\s+chamo|my\s+name\s+is))\s+(?P<name>" + _WORD + r"(?:\s+" + _WORD + r"){0,4})"
)
WEAK_NAME_INTRO = re.compile(
    r"(?i:\b(?:soy|sou|eu\s+sou))\s+(?:(?i:[ao])\s+)?(?P<name>[A-ZÁÉÍÓÚÑÀÂÃÊÔÇ]" + r"[^\W\d_]*(?:['\-][^\W\d_]+)*"
    r"(?:\s+(?:(?:de|del|da|do|dos|das|la)\s+)?[A-ZÁÉÍÓÚÑÀÂÃÊÔÇ][^\W\d_]*(?:['\-][^\W\d_]+)*){0,4})"
)


def _name_span(match: re.Match[str], capitalised_only: bool) -> tuple[int, int] | None:
    words = list(re.finditer(_WORD, match.group("name")))
    kept = []
    for index, word in enumerate(words):
        token = word.group(0)
        if token.lower() in _PARTICLES and kept and index + 1 < len(words) and words[index + 1].group(0)[0].isupper():
            kept.append(word)  # "João da Silva": a particle joins two capitalised words
            continue
        if token.lower() in _NAME_STOP:
            break
        if capitalised_only and not token[0].isupper():
            break
        kept.append(word)
    if not kept or kept[0].group(0).lower() in _ROLE_WORDS:
        return None
    base = match.start("name")
    return base + kept[0].start(), base + kept[-1].end()


def name_findings(text: str) -> list[Finding]:
    found = []
    for pattern, capitalised_only in ((STRONG_NAME_INTRO, False), (WEAK_NAME_INTRO, True)):
        for match in pattern.finditer(text):
            span = _name_span(match, capitalised_only)
            if span is not None:
                found.append(Finding("name", span[0], span[1], text[span[0]:span[1]]))
    return found
