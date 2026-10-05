"""The end-to-end check of scripts/e2e_check.py, with a fake service.

The script runs three modes: the demo cases, the credentials and the access
check. These tests drive each mode against a small HTTP service, so no real app
and no Playwright browser is needed. The phone rule is tested as a pure function.
"""

from __future__ import annotations

import json
import sys
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Self

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import e2e_check


class _Handler(BaseHTTPRequestHandler):
    service: FakeService

    def log_message(self, *args: object) -> None:  # keep the test output clean
        pass

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        if self.path == "/api/v1/auth/demo":
            self._send(200 if self.service.personas else 404, {"personas": []})
        elif self.path == "/api/v1/auth/me":
            login = self.service.last_login or ""
            role, country = self.service.identity.get(login, ("", ""))
            self._send(200, {"role": role, "country": country})
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self) -> None:
        body = self._read()
        if self.path == "/api/v1/auth/login":
            login = body.get("login")
            password = body.get("password")
            if login in self.service.judge and self.service.judge[login] == password:
                self.service.last_login = login
                self._send(200, {"detail": "Logged in"})
            else:
                self._send(401, {"detail": "Invalid credentials"})
        elif self.path == "/api/v1/chat":
            kinds = self.service.chat_kinds
            kind = kinds.popleft() if kinds else "text"
            self._send(200, {"kind": kind})
        else:
            self._send(404, {"detail": "not found"})


class FakeService:
    def __init__(self, *, personas: bool = False) -> None:
        self.personas = personas
        self.judge: dict[str, str] = {}
        self.identity: dict[str, tuple[str, str]] = {}
        self.chat_kinds: deque[str] = deque()
        self.last_login: str | None = None
        handler = type("Handler", (_Handler,), {"service": self})
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> Self:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


# --- the phone rule ---------------------------------------------------------


def test_evaluate_phone_passes_when_every_check_holds() -> None:
    ok, _ = e2e_check.evaluate_phone(
        {
            "no_horizontal_scroll": True,
            "chat_form_visible": True,
            "build_line_visible": True,
            "judge_guide_present": True,
            "judge_guide_open": False,
        }
    )
    assert ok


@pytest.mark.parametrize(
    "broken",
    ["no_horizontal_scroll", "chat_form_visible", "build_line_visible", "judge_guide_present", "judge_guide_open"],
)
def test_evaluate_phone_fails_on_each_broken_check(broken: str) -> None:
    metrics = {
        "no_horizontal_scroll": True,
        "chat_form_visible": True,
        "build_line_visible": True,
        "judge_guide_present": True,
        "judge_guide_open": False,
    }
    metrics[broken] = not metrics[broken]
    ok, detail = e2e_check.evaluate_phone(metrics)
    assert not ok
    assert detail


# --- the credentials file ---------------------------------------------------


def test_load_credentials_reads_login_role_and_password(tmp_path: Path) -> None:
    sheet = tmp_path / "passwords.csv"
    sheet.write_text("login,role,password\nCUST-0001,customer,s3cret\nADV-0001,advisor,other\n", encoding="utf-8")
    records = e2e_check.load_credentials(sheet)
    assert records["CUST-0001"] == {"role": "customer", "password": "s3cret"}
    assert records["ADV-0001"]["role"] == "advisor"


def test_demo_rows_selects_es_mx_and_pt_br() -> None:
    rows = e2e_check.demo_rows()
    assert {row["case"] for row in rows} == {"normal", "ambiguous", "human"}
    assert {row["variant"] for row in rows} == {"es-MX", "pt-BR"}
    assert len(rows) == 6


# --- the cases mode ---------------------------------------------------------


def test_replay_row_passes_with_the_expected_kinds() -> None:
    row = {
        "id": "demo-normal-test",
        "case": "normal",
        "variant": "es-MX",
        "customer": "CUST-0001",
        "steps": [{"message": "hola"}, {"selected_reference": "TXN-1006"}],
        "expect": ["confirm_box", "case_confirmation"],
    }
    with FakeService() as service:
        service.judge["CUST-0001"] = "judge-pass"
        service.chat_kinds.extend(["confirm_box", "case_confirmation"])
        result = e2e_check.replay_row(service.base_url, row, personas=False, credentials={"CUST-0001": {"role": "customer", "password": "judge-pass"}})
    assert result.status == "PASS"


def test_replay_row_fails_when_a_kind_differs() -> None:
    row = {
        "id": "demo-normal-test",
        "case": "normal",
        "variant": "es-MX",
        "customer": "CUST-0001",
        "steps": [{"message": "hola"}],
        "expect": ["confirm_box"],
    }
    with FakeService() as service:
        service.judge["CUST-0001"] = "judge-pass"
        service.chat_kinds.extend(["handoff"])
        result = e2e_check.replay_row(service.base_url, row, personas=False, credentials={"CUST-0001": {"role": "customer", "password": "judge-pass"}})
    assert result.status == "FAIL"
    assert "handoff" in result.detail


def test_replay_row_stops_without_a_credential_for_the_customer() -> None:
    row = {
        "id": "demo-normal-test",
        "case": "normal",
        "variant": "es-MX",
        "customer": "CUST-0002",
        "steps": [{"message": "hola"}],
        "expect": ["confirm_box"],
    }
    result = e2e_check.replay_row("http://127.0.0.1:1", row, personas=False, credentials={})
    assert result.status == "FAIL"
    assert "no judge credential" in result.detail


# --- the access check -------------------------------------------------------


def _credentials() -> dict[str, dict[str, str]]:
    return {
        "CUST-0001": {"role": "customer", "password": "judge-pass"},
        "CUST-0002": {"role": "customer", "password": "judge-pass"},
        "CUST-0003": {"role": "customer", "password": "judge-pass"},
        "ADV-0001": {"role": "advisor", "password": "judge-pass"},
    }


def test_access_check_passes_on_a_locked_link() -> None:
    with FakeService(personas=False) as service:
        service.judge = {login: record["password"] for login, record in _credentials().items()}
        service.identity = dict(e2e_check.EXPECTED_IDENTITY)
        results = e2e_check.access_check(service.base_url, _credentials())
    assert [r.status for r in results] == ["PASS"] * 9


def test_access_check_fails_when_the_persona_route_answers() -> None:
    with FakeService(personas=True) as service:
        service.judge = {login: record["password"] for login, record in _credentials().items()}
        service.identity = dict(e2e_check.EXPECTED_IDENTITY)
        results = e2e_check.access_check(service.base_url, _credentials())
    assert results[0].status == "FAIL"
    assert "200" in results[0].detail


def test_access_check_fails_on_a_wrong_identity() -> None:
    with FakeService(personas=False) as service:
        service.judge = {login: record["password"] for login, record in _credentials().items()}
        service.identity = {"CUST-0001": ("customer", "CO")}
        results = e2e_check.access_check(service.base_url, _credentials())
    assert results[5].status == "FAIL"


# --- the remote stop --------------------------------------------------------


def test_remote_without_credentials_stops_before_a_request(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("SENTINEL_E2E_CREDENTIALS_FILE", raising=False)
    code = e2e_check.main(["--base-url", "https://example.test"])
    assert code == 1
    assert "SENTINEL_E2E_CREDENTIALS_FILE" in capsys.readouterr().err
