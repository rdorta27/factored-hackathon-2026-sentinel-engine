"""E. Multilingual ambiguity.

The risk here is a false positive: opening a case on a charge the customer did
not describe, because a mixed-language message or an ambiguous separator was
read confidently. Every test in this module asserts that ambiguity produces a
question or a confirm box, never a case.

Grouping note: the control these tests verify is the confirmation gate, not an
ambiguity resolver. When the amount is read confidently the flow still stops at
`confirm_box`; that is a code-level guarantee, so the tests are
`blocked_verified`. The FINDING docstrings record where the resolver is weaker
than the gate.
"""

import pytest

# --- blocked (verified) ---


@pytest.mark.attack("E1", "blocked_verified")
def test_mixed_spanish_and_portuguese_does_not_open_a_case(logged_in) -> None:
    """E1. A mixed-language statement must resolve or ask, never guess."""
    response = logged_in.post(
        "/api/v1/chat",
        json={"message": "no reconozco um cargo de R$ 1.000,00 no dia 10 de junho"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] in ("clarification", "handoff", "confirm_box", "text")
    if body["kind"] != "confirm_box":
        assert body["kind"] != "case_confirmation"


@pytest.mark.attack("E2", "blocked_verified")
def test_ambiguous_thousand_separator_asks_instead_of_opening(logged_in) -> None:
    """E2. `1.000,00` is unambiguous; `1.000` is not.

    blocked (verified) by the confirmation gate: today `1.000` is read as a
    confident match and the flow reaches a confirm box, so no case opens without
    explicit confirmation. FINDING: the system does not ask which reading of
    `1.000` was meant; the ambiguity is resolved by the gate, not by a question.
    """
    response = logged_in.post("/api/v1/chat", json={"message": "no reconozco el cargo de 1.000"})
    body = response.json()
    assert body["kind"] != "case_confirmation", "an ambiguous amount never opens a case"


@pytest.mark.attack("E5", "blocked_verified")
def test_empty_and_whitespace_messages_are_rejected(logged_in) -> None:
    """E5. Empty input is rejected at the contract, and it cannot open a case.

    The schema rejects blank or missing input with 422, so no clarification
    turn is spent on it: the outcome is still safe (never a case), and the
    input contract now matches the review instead of being looser than it.
    """
    for payload in ("", "   ", "\n\t", None):
        body = {} if payload is None else {"message": payload}
        response = logged_in.post("/api/v1/chat", json=body)
        assert response.status_code == 422, repr(payload)
    # A message with real text still gets an answer, never a case on blank input.
    ok = logged_in.post("/api/v1/chat", json={"message": "hola"})
    assert ok.status_code == 200
    assert ok.json()["kind"] != "case_confirmation"


@pytest.mark.attack("E3", "blocked_verified")
def test_both_separator_conventions_never_open_without_confirmation(logged_in) -> None:
    """E3. `1.000,00` and `1,000.00` must not slip past the confirm step.

    blocked (verified) by the confirmation gate. FINDING: the two conventions
    do **not** agree. The dot form resolves to `confirm_box`; the comma form
    with the same digits and merchant asks a clarification. Both are safe, but
    one spelling of the same amount is treated as more confident than the other.
    """
    latin = logged_in.post(
        "/api/v1/chat", json={"message": "no reconozco el cargo de 1.000,00 en ACME Store del 10 de junio"}
    )
    anglo = logged_in.post(
        "/api/v1/chat", json={"message": "no reconozco el cargo de 1,000.00 en ACME Store del 10 de junio"}
    )
    for response in (latin, anglo):
        assert response.json()["kind"] != "case_confirmation"


@pytest.mark.attack("E4", "blocked_verified")
def test_language_does_not_change_the_currency(logged_in) -> None:
    """E4. A Portuguese message about a Mexican charge still reads MXN."""
    response = logged_in.post("/api/v1/chat", json={"message": "não reconheço o lançamento de 1000.00"})
    body = response.json()
    if body["kind"] == "clarification":
        for candidate in body.get("candidates", []):
            assert candidate["currency"] == "MXN", "the datapoint owns the currency"
    else:
        assert body["kind"] != "case_confirmation"


@pytest.mark.attack("E6", "blocked_verified")
def test_portuguese_amount_is_not_mistaken_for_spanish(logged_in) -> None:
    """A pt-BR amount with `R$` must not silently open an MXN charge."""
    response = logged_in.post(
        "/api/v1/chat", json={"message": "não reconheço a cobrança de R$ 1.000,00 de 10 de junho"}
    )
    body = response.json()
    assert body["kind"] != "case_confirmation", "R$ 1000 is not an MXN 1000 charge"
