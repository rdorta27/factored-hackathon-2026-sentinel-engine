"""Whole numbers in words for es-419 and pt-BR: a writer and a reader.

The writer builds the phrasing of the charge-ranker examples. The reader gives
the selector a clue when a customer states an amount in words ("cuatrocientos
cuarenta y tres"). Both cover 0 to 999,999,999 and need no dependency.
"""

from __future__ import annotations

import re
from typing import Literal

from app.ai.grounding import normalize_text

Lang = Literal["es", "pt"]

_ES_UNITS = (
    "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince "
    "dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro "
    "veinticinco veintiséis veintisiete veintiocho veintinueve"
).split()
_ES_TENS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_ES_HUNDREDS = {
    1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos",
    6: "seiscientos", 7: "setecientos", 8: "ochocientos", 9: "novecientos",
}
_PT_UNITS = (
    "zero um dois três quatro cinco seis sete oito nove dez onze doze treze quatorze quinze "
    "dezesseis dezessete dezoito dezenove"
).split()
_PT_TENS = {
    2: "vinte", 3: "trinta", 4: "quarenta", 5: "cinquenta", 6: "sessenta", 7: "setenta",
    8: "oitenta", 9: "noventa",
}
_PT_HUNDREDS = {
    1: "cento", 2: "duzentos", 3: "trezentos", 4: "quatrocentos", 5: "quinhentos",
    6: "seiscentos", 7: "setecentos", 8: "oitocentos", 9: "novecentos",
}


def _es_below_thousand(n: int) -> str:
    if n == 100:
        return "cien"
    parts = []
    if n >= 100:
        parts.append(_ES_HUNDREDS[n // 100])
        n %= 100
    if n == 0:
        return " ".join(parts)
    if n < 30:
        parts.append(_ES_UNITS[n])
    else:
        tens, unit = divmod(n, 10)
        parts.append(_ES_TENS[tens] + (f" y {_ES_UNITS[unit]}" if unit else ""))
    return " ".join(parts)


def _es_apocope(words: str) -> str:
    """Before "mil" and "millones", "uno" becomes "un" and "veintiuno" becomes "veintiún"."""
    if words.endswith("veintiuno"):
        return words[: -len("veintiuno")] + "veintiún"
    if words.endswith("uno"):
        return words[:-1]
    return words


def _pt_below_thousand(n: int) -> str:
    if n == 100:
        return "cem"
    parts = []
    if n >= 100:
        parts.append(_PT_HUNDREDS[n // 100])
        n %= 100
    if n == 0:
        return " e ".join(parts)
    if n < 20:
        parts.append(_PT_UNITS[n])
    else:
        tens, unit = divmod(n, 10)
        parts.append(_PT_TENS[tens] + (f" e {_PT_UNITS[unit]}" if unit else ""))
    return " e ".join(parts)


def number_to_words(value: int, lang: Lang) -> str:
    if not 0 <= value < 1_000_000_000:
        raise ValueError("value out of range")
    if value == 0:
        return "cero" if lang == "es" else "zero"
    below = _es_below_thousand if lang == "es" else _pt_below_thousand
    millions, rest = divmod(value, 1_000_000)
    thousands, units = divmod(rest, 1000)
    parts: list[str] = []
    if millions:
        if lang == "es":
            parts.append("un millón" if millions == 1 else f"{_es_apocope(below(millions))} millones")
        else:
            parts.append("um milhão" if millions == 1 else f"{below(millions)} milhões")
    if thousands:
        if thousands == 1:
            parts.append("mil")
        else:
            head = below(thousands)
            parts.append(f"{_es_apocope(head) if lang == 'es' else head} mil")
    if units:
        parts.append(below(units))
    if lang == "pt" and len(parts) > 1 and (units < 100 or units % 100 == 0) and units:
        return " ".join(parts[:-1]) + " e " + parts[-1]
    return " ".join(parts)


def _table(units: list[str], tens: dict[int, str], hundreds: dict[int, str], start: int) -> dict[str, int]:
    out = {normalize_text(word): index for index, word in enumerate(units) if index >= start}
    out.update({normalize_text(word): tens_value * 10 for tens_value, word in tens.items()})
    out.update({normalize_text(word): hundreds_value * 100 for hundreds_value, word in hundreds.items()})
    out["cien"] = 100
    out["cem"] = 100
    return out


_VALUES: dict[str, int] = {
    **_table(_ES_UNITS, _ES_TENS, _ES_HUNDREDS, 1),
    **_table(_PT_UNITS, _PT_TENS, _PT_HUNDREDS, 1),
    "un": 1, "una": 1, "veintiun": 21, "um": 1, "uma": 1, "dois": 2, "duas": 2,
    "catorze": 14, "quatorze": 14, "dezasseis": 16, "dezanove": 19,
}
_CONNECTORS = frozenset({"y", "e"})
_AFTER_NOT_AMOUNT = frozenset({
    "de", "dia", "dias", "vez", "veces", "vezes", "ano", "anos", "mes", "meses", "hora", "horas",
    "semana", "semanas",
})
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def words_to_numbers(text: str) -> list[int]:
    """Whole numbers of 10 or more that the text writes in words.

    A run followed by "de", "dias" or similar is a date or a count, not an amount.
    "una compra" is not an amount: a run below 10 is dropped.
    """
    tokens = _TOKEN_RE.findall(normalize_text(text))
    found: list[int] = []
    index = 0
    while index < len(tokens):
        if tokens[index] not in _VALUES and tokens[index] not in ("mil", "millon", "millones", "milhao", "milhoes"):
            index += 1
            continue
        total = current = 0
        end = index
        while end < len(tokens):
            token = tokens[end]
            if token in _VALUES:
                current += _VALUES[token]
            elif token == "mil":
                total += (current or 1) * 1000
                current = 0
            elif token in ("millon", "milhao"):
                total += (current or 1) * 1_000_000
                current = 0
            elif token in ("millones", "milhoes"):
                total += current * 1_000_000
                current = 0
            elif token in _CONNECTORS and end + 1 < len(tokens) and (
                tokens[end + 1] in _VALUES or tokens[end + 1] == "mil"
            ):
                pass
            else:
                break
            end += 1
        value = total + current
        follower = tokens[end] if end < len(tokens) else ""
        if value >= 10 and follower not in _AFTER_NOT_AMOUNT:
            found.append(value)
        index = max(end, index + 1)
    return found


_MULTIPLIERS = frozenset({"mil", "millon", "millones", "milhao", "milhoes", "y", "e"})


def is_number_word(token: str) -> bool:
    """True for a word that writes part of a number, so it is not a merchant name."""
    token = normalize_text(token)
    return token in _VALUES or token in _MULTIPLIERS
