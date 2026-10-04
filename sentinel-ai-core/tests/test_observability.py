"""Acceptance tests for the structured turn log (observability)."""

import json
import os

import pytest

from app.observability import StepRecord


def _valid(**overrides):  # type: ignore[no-untyped-def]
    fields = {
        "ts": "2026-09-30T15:00:00+00:00",
        "trace_id": "a1b2c3d4e5f60718",
        "session_ref": "9f8e7d6c5b4a3928",
        "step": "decide",
        "tool": None,
        "outcome": "ok",
        "attempt": 1,
        "policy_rule": "status.explain.reversed",
        "latency_ms": 3.2,
        "model": "fake",
        "route": "mock",
        "prompt_version": "none",
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_usd": 0.0,
        "language": "es-419",
        "country": "MX",
    }
    fields.update(overrides)
    return StepRecord(**fields)


def test_record_serializes_to_stable_json() -> None:
    line = _valid().to_json()
    body = json.loads(line)
    assert body["trace_id"] == "a1b2c3d4e5f60718"
    assert body["tool"] is None
    assert body["policy_rule"] == "status.explain.reversed"


@pytest.mark.parametrize(
    "field,value",
    [
        ("tool", "lookup for CUST-0001"),
        ("policy_rule", "CUST-0002.allow"),
        ("model", "CUST-0003"),
        ("event", "login from 192.168.0.10"),
        ("route", "10.0.0.1"),
        ("tool", "lookup for CLI-AB12CD34"),
    ],
)
def test_record_rejects_pii(field: str, value: str) -> None:
    with pytest.raises(ValueError, match="personal data is never logged"):
        _valid(**{field: value})


def test_record_rejects_a_dataset_customer_id() -> None:
    with pytest.raises(ValueError, match="personal data is never logged"):
        _valid(handoff={"note": "CLI-AB12CD34"})


def test_record_rejects_bad_identifiers_and_enums() -> None:
    with pytest.raises(ValueError, match="trace_id"):
        _valid(trace_id="unknown")
    with pytest.raises(ValueError, match="session_ref"):
        _valid(session_ref="CUST-0001")
    with pytest.raises(ValueError, match="step"):
        _valid(step="think")
    with pytest.raises(ValueError, match="outcome"):
        _valid(outcome="maybe")
    with pytest.raises(ValueError, match="attempt"):
        _valid(attempt=0)
    with pytest.raises(ValueError, match="never empty"):
        _valid(model="")
    with pytest.raises(ValueError, match="label"):
        _valid(label="refund")
    with pytest.raises(ValueError, match="confidence"):
        _valid(confidence=1.5)


def test_record_serializes_label_and_confidence() -> None:
    body = json.loads(_valid(step="understand", label="charge", confidence=0.87).to_json())
    assert body["label"] == "charge"
    assert body["confidence"] == 0.87
    assert json.loads(_valid().to_json())["confidence"] is None


def _logged_in_client(tmp_path):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.observability import Recorder

    api = TestClient(create_app())
    api.app.state.recorder = Recorder(path=tmp_path / "turns.jsonl", salt="test-salt")
    assert (
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    return api


def test_text_turn_leaves_a_complete_trace(tmp_path) -> None:
    api = _logged_in_client(tmp_path)
    response = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    assert response.status_code == 200
    trace_id = response.headers["X-Trace-Id"]

    records = api.app.state.recorder.records_for(trace_id)
    assert records, "a text turn must leave records"
    assert {record.step for record in records} >= {"understand", "turn"}
    closing = next(record for record in records if record.step == "turn")
    assert closing.outcome == "ok"
    assert isinstance(closing.latency_ms, float)


def test_failing_turn_still_leaves_a_closing_record(tmp_path) -> None:
    api = _logged_in_client(tmp_path)
    response = api.post("/api/v1/chat", json={"selected_reference": "TXN-9999"})
    assert response.status_code == 200
    trace_id = response.headers["X-Trace-Id"]

    records = api.app.state.recorder.records_for(trace_id)
    closing = [record for record in records if record.step == "turn"]
    assert len(closing) == 1
    assert closing[0].policy_rule == "unknownCharge"


def test_full_turn_is_replayable_by_trace_id(tmp_path) -> None:
    from fastapi.testclient import TestClient

    from app.main import SESSION_COOKIE, create_app
    from app.observability import Recorder

    api = TestClient(create_app())
    recorder = Recorder(path=tmp_path / "turns.jsonl", salt="acceptance")
    api.app.state.recorder = recorder
    api.app.state.audit.recorder = recorder
    message = "no reconozco un cargo"
    assert (
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    assert api.post("/api/v1/chat", json={"message": message}).status_code == 200
    assert api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).status_code == 200
    confirmed = api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    assert confirmed.json()["kind"] == "case_confirmation"

    trace_id = confirmed.headers["X-Trace-Id"]
    records = recorder.records_for(trace_id)
    steps = {record.step for record in records}
    assert {"decide", "act", "verify", "turn"} <= steps
    assert any(
        record.step == "decide" and record.policy_rule is not None for record in records
    )
    closing = next(record for record in records if record.step == "turn")
    assert closing.outcome == "ok"
    assert isinstance(closing.cost_usd, float)
    assert isinstance(closing.latency_ms, float)

    lines = (tmp_path / "turns.jsonl").read_text(encoding="utf-8").splitlines()
    replayed = [json.loads(line) for line in lines if json.loads(line)["trace_id"] == trace_id]
    assert len(replayed) == len(records)
    blob = "\n".join(lines)
    token = api.cookies.get(SESSION_COOKIE)
    for forbidden in ("CUST-0001", "Testpass-001", message, token):
        assert forbidden not in blob


def test_stdout_line_matches_the_file_and_omits_customer_id(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("SENTINEL_LOG_STDOUT", "1")
    monkeypatch.setenv("SENTINEL_VAR_DIR", str(tmp_path / "var"))
    monkeypatch.setenv("SENTINEL_DB_PATH", str(tmp_path / "state.db"))
    from fastapi.testclient import TestClient

    from app.main import create_app

    api = TestClient(create_app())
    assert (
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    assert api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}).status_code == 200

    captured = capsys.readouterr().out
    file_lines = (tmp_path / "var" / "turns.jsonl").read_text(encoding="utf-8").splitlines()
    stdout_lines = [line for line in captured.splitlines() if line.startswith("{")]
    assert stdout_lines == file_lines
    assert stdout_lines
    assert "CUST-0001" not in captured
    assert "Testpass-001" not in captured


def test_stdout_is_off_when_unset(tmp_path, monkeypatch, capsys) -> None:
    from app.observability import Recorder

    monkeypatch.delenv("SENTINEL_LOG_STDOUT", raising=False)
    recorder = Recorder(path=tmp_path / "turns.jsonl", salt="test-salt")
    recorder.emit(_valid())
    assert capsys.readouterr().out == ""
    assert (tmp_path / "turns.jsonl").read_text(encoding="utf-8").strip() == _valid().to_json()


def test_writer_round_trips_both_sinks(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.observability import Recorder

    recorder = Recorder(path=tmp_path / "turns.jsonl", salt="test-salt")
    first = _valid(trace_id="0" * 16)
    second = _valid(trace_id="f" * 16)
    recorder.emit(first)
    recorder.emit(second)

    assert recorder.records == [first, second]
    assert recorder.records_for("0" * 16) == [first]
    lines = (tmp_path / "turns.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["trace_id"] for line in lines] == ["0" * 16, "f" * 16]


def test_persisted_for_reads_a_trace_back_after_a_restart(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.observability import Recorder

    path = tmp_path / "turns.jsonl"
    written = Recorder(path=path, salt="test-salt")
    written.emit(_valid(trace_id="a" * 16))
    written.emit(_valid(trace_id="b" * 16, step="escalate"))

    # A new process: nothing in memory, the log still holds the trace.
    fresh = Recorder(path=path, salt="test-salt")
    assert fresh.records_for("a" * 16) == []
    loaded = fresh.persisted_for("a" * 16)
    assert [record.step for record in loaded] == ["decide"]
    assert loaded[0].trace_id == "a" * 16
    assert fresh.persisted_for("c" * 16) == []


def test_session_ref_is_stable_and_not_the_identifier() -> None:
    from app.observability import Recorder

    recorder = Recorder(path=None, salt="test-salt")
    ref = recorder.session_ref("CUST-0001")
    assert ref == recorder.session_ref("CUST-0001")
    assert "CUST-0001" not in ref
    assert len(ref) == 16


def test_dev_salt_persists_across_restarts(tmp_path, monkeypatch) -> None:
    from app.observability import Recorder

    monkeypatch.delenv("SENTINEL_SESSION_SALT", raising=False)
    monkeypatch.setenv("SENTINEL_VAR_DIR", str(tmp_path / "var"))
    first = Recorder()
    second = Recorder()
    assert first.salt == second.salt
    assert first.session_ref("CUST-0001") == second.session_ref("CUST-0001")
    assert (tmp_path / "var" / ".session_salt").is_file()


@pytest.mark.skipif(
    os.name == "nt", reason="POSIX file modes are not enforced on Windows"
)
def test_turn_log_and_dev_salt_are_owner_only(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import os
    import stat

    from app.observability import Recorder

    monkeypatch.delenv("SENTINEL_SESSION_SALT", raising=False)
    monkeypatch.setenv("SENTINEL_VAR_DIR", str(tmp_path / "var"))
    Recorder()
    for name in ("turns.jsonl", ".session_salt"):
        mode = stat.S_IMODE(os.stat(tmp_path / "var" / name).st_mode)
        assert mode == 0o600, name


def test_var_dir_ignores_process_cwd(tmp_path, monkeypatch) -> None:
    from app.observability import var_dir

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SENTINEL_VAR_DIR", raising=False)
    assert var_dir().parent.name == "sentinel-ai-core"
    assert var_dir().name == "var"


def test_decide_records_the_policy_version(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import shutil

    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.observability import Recorder
    from app.orchestrator import step as step_module
    from app.policy.load import CONFIG_DIR, load_country

    policy_dir = tmp_path / "policy"
    shutil.copytree(CONFIG_DIR, policy_dir)
    monkeypatch.setattr(step_module, "load_country", lambda country: load_country(country, policy_dir))

    api = TestClient(create_app())
    recorder = Recorder(path=tmp_path / "turns.jsonl", salt="policy-version")
    api.app.state.recorder = recorder
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code == 200

    def decide_versions(response):  # type: ignore[no-untyped-def]
        records = recorder.records_for(response.headers["X-Trace-Id"])
        return {(r.policy_version, r.policy_synthetic) for r in records if r.step == "decide"}

    first = decide_versions(api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}))
    mx = policy_dir / "mx.yaml"
    mx.write_text(mx.read_text(encoding="utf-8") + "# value changed\n", encoding="utf-8")
    second = decide_versions(api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}))

    assert len(first) == 1 and len(second) == 1
    (old_version, old_synthetic), (new_version, _) = first.pop(), second.pop()
    assert old_version and new_version and old_version != new_version
    assert old_synthetic is True
