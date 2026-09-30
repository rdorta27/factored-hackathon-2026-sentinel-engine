"""Acceptance tests for the structured turn log (observability)."""

import json

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
    ],
)
def test_record_rejects_pii(field: str, value: str) -> None:
    with pytest.raises(ValueError, match="personal data is never logged"):
        _valid(**{field: value})


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


def test_session_ref_is_stable_and_not_the_identifier() -> None:
    from app.observability import Recorder

    recorder = Recorder(path=None, salt="test-salt")
    ref = recorder.session_ref("CUST-0001")
    assert ref == recorder.session_ref("CUST-0001")
    assert "CUST-0001" not in ref
    assert len(ref) == 16
