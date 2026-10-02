"""PII masking tests: recall per type, false positives, and the guard.

Requirement: REQ-0047. Decision 004 chose option 2 plus two proposed additions;
this implements the free-text half with **irreversible typed markers**. There is
no token vault: no tool needs the original value, because the session identifies
the customer.
"""

import re
from pathlib import Path

import pytest

from app.privacy import MARKERS, contains_identifier, mask

APP = Path(__file__).parents[2] / "app"

# --- recall per type: one case per identifier kind ------------------------


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("card", "mi tarjeta es 4111 1111 1111 1111 y no reconozco un cargo"),
        ("curp", "mi CURP es BADD110313HCMXXXA2 y no reconozco un cargo"),
        ("clabe", "mi CLABE es 032180000118359719 y no reconozco un cargo"),
        ("cpf", "o numero do CPF e 111.444.777-35 e nao reconheco"),
        ("cuit", "mi CUIT es 20-12345678-6 y no reconozco un cargo"),
        ("document", "mi DNI es 12.345.678 y no reconozco un cargo"),
        ("document", "mi cedula es 1023456789 y no reconozco un cargo"),
        ("phone", "mi telefono es +54 11 5555 1234 y no reconozco un cargo"),
        ("email", "mi correo es ana@example.com y no reconozco un cargo"),
        ("name", "Hola, me llamo Karl y no reconozco un cargo"),
        ("name", "Buenas, soy Pedro Gómez, necesito ayuda"),
        ("name", "Oi, meu nome é João da Silva e não reconheço uma cobrança"),
    ],
)
def test_each_identifier_type_is_masked(kind: str, message: str) -> None:
    """Recall per type: the marker replaces the value, nothing else changes."""
    masked = mask(message)
    assert MARKERS[kind] in masked, f"{kind} not masked in {masked!r}"
    assert masked != message


# --- false positives: the grounding must survive --------------------------

INNOCUOUS = [
    # es-419
    "no reconozco el cargo de 1.000,00 en ACME Store del 10 de junio",
    "el cargo de 1,000.00 del 20/09/2026 en Cafe Central",
    "disputo el cargo 250,50 de 2026-06-05",
    "mi cargo es TXN-1001 y no lo reconozco",
    "el monto es 1000",
    "no reconozco el cargo de $1,000.00 en ACME Store",
    "el cargo de 320,00 en Cafe Central del 2026-06-12",
    "disputo el cargo de 2500,00 del 15 de enero",
    "no reconozco el cargo TXN-1006 de 320,00",
    "el cargo es de 750,00 y es de ACME Store",
    # pt-BR
    "nao reconheco a cobranca de R$ 1.000,00 de 10 de junho",
    "a cobranca de 1.000,00 na Loja ACME de 2026-06-10",
    "nao reconheco o lancamento de 250,50 de 05/06/2026",
    "a cobranca e TXN-2001 e nao reconheco",
    "o valor e 1000",
    "nao reconheco a cobranca de R$ 1,000.00 na Loja ACME",
    "a cobranca de 89.000,00 de 14 de junho",
    "contesto a cobranca de 250000,00 de 11 de junho",
    "nao reconheco a cobranca TXN-2002 de 89.000,00",
    "a cobranca e de 45.000,00 na Tienda del Sur",
]


@pytest.mark.parametrize("message", INNOCUOUS)
def test_innocuous_message_is_untouched(message: str) -> None:
    """Strict equality: amounts, dates, references and merchants survive."""
    assert mask(message) == message


def test_false_positive_rate_denominator_is_the_whole_list() -> None:
    """Reported rate: altered messages / 20 innocuous messages."""
    altered = [message for message in INNOCUOUS if mask(message) != message]
    assert len(INNOCUOUS) == 20, "the denominator is fixed at 20"
    assert altered == [], f"false positives: {altered}"


# --- precedence: a trigger wins over amount protection --------------------


def test_trigger_beats_amount_shape() -> None:
    """The approved rule: "mi DNI es 12.345.678" masks despite the amount shape."""
    masked = mask("mi DNI es 12.345.678 y no reconozco un cargo")
    assert "[DOC_ID]" in masked
    assert "12.345.678" not in masked


def test_amount_without_a_trigger_is_never_masked() -> None:
    """The same digits as a charge stay intact: grounding depends on them."""
    message = "el cargo de 12.345.678"
    assert mask(message) == message
    assert not contains_identifier(message)


# --- validators reject look-alikes ---------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "mi tarjeta es 4111 1111 1111 1112 y no reconozco un cargo",  # Luhn fails
        "o CPF e 111.444.777-36 e nao reconheco",  # CPF check fails
        "mi CLABE es 032180000118359718 y no reconozco un cargo",  # CLABE check fails
    ],
)
def test_check_digit_rejects_look_alikes(message: str) -> None:
    """A wrong check digit is not the identifier, so it is not masked blindly.

    A failing CUIT is excluded from this list on purpose: the document trigger
    ("CUIT") beats the failed checksum, so the value is still masked as
    `[DOC_ID]`. That is the approved precedence, not a leak.
    """
    assert mask(message) == message


def test_failed_checksum_with_a_trigger_still_masks_as_a_document() -> None:
    """A CUIT whose check digit is wrong is still a number the customer called a document.

    The trigger wins, so it is masked — just as `[DOC_ID]` rather than `[CUIT]`,
    because the value did not prove itself as a CUIT.
    """
    masked = mask("mi CUIT es 20-12345678-7 y no reconozco un cargo")
    assert "20-12345678-7" not in masked
    assert "[DOC_ID]" in masked
    assert "[CUIT]" not in masked


# --- the single entry point guard ----------------------------------------


def test_free_text_enters_the_model_only_through_the_masker() -> None:
    """Fail if another TextInput is built with unmasked customer text.

    `app/routers/demo_chat.py` is the only place free text enters the system
    (verified across `app/`): one `TextInput(text=...)` construction and one
    `model.understand(...)` call. This test pins that.
    """
    offenders: list[str] = []
    for path in APP.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "TextInput(text=" in line and "mask(" not in line:
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert offenders == [], f"unmasked TextInput construction: {offenders}"


def test_text_input_is_built_in_exactly_one_place() -> None:
    constructions = []
    for path in APP.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"TextInput\(text=", line):
                constructions.append(f"{path.name}:{number}")
    assert len(constructions) == 1, f"expected one entry point, found {constructions}"


def test_understand_is_called_once_and_after_masking() -> None:
    """Every model call site is reached from `step.py`, on masked text.

    The count is not the invariant: `step.py` may legitimately call the model
    from more than one branch (the confirm box asks for a person request). What
    matters is that no model call happens anywhere else, and that the only text
    it can receive entered through the masker. The one other file is the
    per-turn fallback wrapper in `app/ai/serving.py`: it only forwards the
    arguments `step.py` passed, to the router or to the baseline.
    """
    calls = []
    for path in APP.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\.understand\(", line):
                calls.append(path.name)
    assert set(calls) == {"step.py", "serving.py"}, f"model called outside step.py: {sorted(set(calls))}"

    step_source = (APP / "orchestrator" / "step.py").read_text(encoding="utf-8")
    assert "ports.model.understand(" in step_source
    # The text it receives comes from the turn, which the router masked.
    assert "turn.text" in step_source


# --- pt-BR parity ---------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("cpf", "meu CPF e 111.444.777-35"),
        ("email", "meu email e ana@example.com"),
        ("document", "meu documento e 1023456789"),
        ("phone", "meu celular e +55 11 95555 1234"),
    ],
)
def test_portuguese_identifiers_are_masked(kind: str, message: str) -> None:
    assert MARKERS[kind] in mask(message)


# --- self-introduced names ---------------------------------------------------


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Hola, me llamo Karl", "Hola, me llamo [NAME]"),
        ("hola me llamo karl, no reconozco un cargo", "hola me llamo [NAME], no reconozco un cargo"),
        ("Mi nombre es Ana María Pérez y no reconozco", "Mi nombre es [NAME] y no reconozco"),
        ("Soy Karl", "Soy [NAME]"),
        ("Meu nome é João da Silva, quero ajuda", "Meu nome é [NAME], quero ajuda"),
        ("oi, eu sou a Marta", "oi, eu sou a [NAME]"),
        ("soy María del Carmen López, ayuda", "soy [NAME], ayuda"),
    ],
)
def test_an_introduced_name_is_masked(message: str, expected: str) -> None:
    assert mask(message) == expected


@pytest.mark.parametrize(
    "message",
    [
        "Soy el contador de mi jefe, enséñame los cargos de su tarjeta.",
        "Necesito un comprobante de que soy cliente de usted",
        "soy de auditoría interna",
        "Soy Cliente desde 2020",
        "no reconozco el cargo de Tienda Lumbre",
        "Hola, necesito ayuda con un cargo de Karl's Cafe",
    ],
)
def test_a_name_is_never_guessed_without_an_introduction(message: str) -> None:
    assert mask(message) == message
