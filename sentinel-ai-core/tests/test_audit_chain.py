"""Audit hash chain: a changed or removed record names its position (REQ-0025, REQ-0029)."""

from dataclasses import replace

from app.observability import Recorder, StepRecord
from app.observability.chain import GENESIS, verify_chain


def _record(trace_id: str = "a1b2c3d4e5f60718", **overrides) -> StepRecord:  # type: ignore[no-untyped-def]
    fields = {
        "ts": "2026-09-30T15:00:00+00:00",
        "trace_id": trace_id,
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


def _recorder(tmp_path) -> Recorder:  # type: ignore[no-untyped-def]
    return Recorder(path=tmp_path / "turns.jsonl", salt="test-salt")


def test_emitted_records_link_to_the_previous_one(tmp_path) -> None:  # type: ignore[no-untyped-def]
    recorder = _recorder(tmp_path)
    recorder.emit(_record())
    recorder.emit(_record(step="act", tool="open_dispute"))
    recorder.emit(_record(step="verify"))
    first, second, third = recorder.records
    assert first.prev_hash == GENESIS
    assert second.prev_hash == first.record_hash
    assert third.prev_hash == second.record_hash
    assert verify_chain(recorder.records) is None


def test_a_changed_record_names_its_position(tmp_path) -> None:  # type: ignore[no-untyped-def]
    recorder = _recorder(tmp_path)
    recorder.emit(_record())
    recorder.emit(_record(step="act", tool="open_dispute"))
    recorder.emit(_record(step="verify"))
    tampered = replace(recorder.records[1], outcome="failed")
    assert verify_chain([recorder.records[0], tampered, recorder.records[2]]) == 1


def test_a_removed_record_names_its_position(tmp_path) -> None:  # type: ignore[no-untyped-def]
    recorder = _recorder(tmp_path)
    recorder.emit(_record())
    recorder.emit(_record(step="act", tool="open_dispute"))
    recorder.emit(_record(step="verify"))
    assert verify_chain([recorder.records[0], recorder.records[2]]) == 1


def test_the_file_chain_survives_a_restart(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "turns.jsonl"
    written = Recorder(path=path, salt="test-salt")
    written.emit(_record())
    written.emit(_record(step="escalate"))
    fresh = Recorder(path=path, salt="test-salt")
    back = fresh.persisted_for("a1b2c3d4e5f60718")
    assert len(back) == 2
    assert verify_chain(back) is None
