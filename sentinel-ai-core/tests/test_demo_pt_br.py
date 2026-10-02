"""Demo scripts in four variants, plus pt-BR baseline probes.

The scripts live in eval/demo/pt-br.jsonl so the video sheet and the next
router branch replay the same turns. Tests assert outcome kind, not wording.
The account stays with the charge; the variant is the wording. Pix is out of
scope as a word. extrato and fatura stay charge vocabulary.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.ai.demo import DemoModel
from app.ai.port import UnderstandKind
from app.main import create_app
from app.schemas.chat import Handoff

PASSWORD = "Testpass-001"
SCRIPTS = Path(__file__).resolve().parents[1] / "eval" / "demo" / "pt-br.jsonl"
I18N = Path(__file__).resolve().parents[1] / "app" / "static" / "i18n"


def _load() -> list[dict]:
    rows = [json.loads(line) for line in SCRIPTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows, "demo scripts missing"
    assert "sealed" not in SCRIPTS.parts
    return rows


def _replay(row: dict) -> list[dict]:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": row["customer"], "password": PASSWORD}).status_code == 200
    replies = []
    for step in row["steps"]:
        response = api.post("/api/v1/chat", json=step)
        assert response.status_code == 200, step
        replies.append(response.json())
    return replies


def test_scripts_are_development_simulation() -> None:
    for row in _load():
        assert row["split"] == "development"
        assert row["origin"] == "team-written-simulation"
        assert row["block"] in {"demo", "probe"}


def test_four_variants_of_each_demo_case_pass_on_the_baseline() -> None:
    demos = [row for row in _load() if row["block"] == "demo"]
    assert len(demos) == 12
    by_case: dict[str, list[str]] = {}
    for row in demos:
        by_case.setdefault(row["case"], []).append(row["variant"])
    assert by_case == {
        "normal": ["es-MX", "es-CO", "es-AR", "pt-BR"],
        "ambiguous": ["es-MX", "es-CO", "es-AR", "pt-BR"],
        "human": ["es-MX", "es-CO", "es-AR", "pt-BR"],
    }
    customers = {row["case"]: row["customer"] for row in demos}
    assert customers == {"normal": "CUST-0001", "ambiguous": "CUST-0002", "human": "CUST-0003"}
    for row in demos:
        replies = _replay(row)
        assert [reply["kind"] for reply in replies] == row["expect"], row["id"]
        assert all(reply["kind"] != "case_confirmation" or reply is replies[-1] for reply in replies)
        if row["case"] == "normal":
            box, case = replies
            assert box["candidate"]["merchant"] == row["merchant"]
            assert box["candidate"]["currency"] == row["currency"]
            assert case["verified"] is True and case["source"] == "mock"
            assert case["transaction"]["currency"] == "MXN"
            assert "R$" not in row["steps"][0]["message"]
            if row["variant"] != "pt-BR":
                spoken = row["steps"][0]["message"]
                assert "pesos mexicanos" in spoken
                assert "MXN" not in spoken
        if row["case"] == "ambiguous":
            assert replies[0]["candidates"]
            assert all(reply["kind"] != "case_confirmation" for reply in replies)
        if row["case"] == "human":
            package = Handoff.model_validate(replies[-1]).package
            assert package.language == row["language"]
            assert package.country == row["country"]
            assert package.request == row["request"]


def test_probes_lock_baseline_behavior() -> None:
    by_id = {row["id"]: row for row in _load()}

    unrecognized = _replay(by_id["probe-unrecognized"])
    assert unrecognized[0]["kind"] == "confirm_box"
    assert unrecognized[0]["kind"] != "handoff"

    claim = _replay(by_id["probe-not-mine"])
    assert [reply["kind"] for reply in claim] == ["clarification", "handoff"]
    assert Handoff.model_validate(claim[-1]).package.conversation[-1].rule == "fraud.claim"

    brl = _replay(by_id["probe-brl-amount"])
    assert brl[0]["kind"] != "case_confirmation"
    if brl[0]["kind"] == "confirm_box":
        assert brl[0]["candidate"]["currency"] == "MXN"

    saldo = _replay(by_id["probe-saldo"])
    assert saldo[0]["kind"] == "text"
    assert saldo[0]["message_key"] == "out_of_scope.ask"


def test_pix_abstains_and_statement_words_show_account_charges() -> None:
    by_id = {row["id"]: row for row in _load()}
    pix = _replay(by_id["probe-pix"])
    assert pix[0]["kind"] == "text"
    assert pix[0]["message_key"] == "out_of_scope.ask"
    assert DemoModel().understand("cargo en PIXELMART", []).kind is UnderstandKind.CHARGE
    for case_id in ("probe-extrato", "probe-fatura"):
        replies = _replay(by_id[case_id])
        assert replies[0]["kind"] == "clarification"
        assert replies[0]["candidates"]


def test_person_button_phrase_is_in_the_locale_file() -> None:
    es = json.loads((I18N / "es-419.json").read_text(encoding="utf-8"))
    pt = json.loads((I18N / "pt-BR.json").read_text(encoding="utf-8"))
    ar = json.loads((I18N / "es-AR.json").read_text(encoding="utf-8"))
    assert es["agentMessage"] == "quiero una persona"
    assert pt["agentMessage"] == "quero falar com um atendente"
    assert "agentMessage" not in ar
    api = TestClient(create_app())
    assert api.get("/i18n/es-AR").json()["agentMessage"] == es["agentMessage"]
    assert api.get("/i18n/pt-BR").json()["agentMessage"] == pt["agentMessage"]
