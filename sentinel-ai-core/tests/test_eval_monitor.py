"""Country monitoring: aggregates only, unknown countries apart, write-once."""

import json

import pytest

from eval.monitor import freeze_monitoring, render_report, summarize


def _record(trace: str, step: str, country: str = "MX", language: str = "es-419", **over):  # type: ignore[no-untyped-def]
    body = {
        "ts": "2026-10-02T10:00:00+00:00",
        "trace_id": f"trace-{trace}",
        "session_ref": f"session-{trace}",
        "step": step,
        "tool": None,
        "outcome": "ok",
        "attempt": 1,
        "policy_rule": None,
        "latency_ms": 40.0,
        "model": "fake",
        "route": "mock",
        "prompt_version": "none",
        "tokens_in": 10,
        "tokens_out": 5,
        "cost_usd": 0.0001,
        "language": language,
        "country": country,
        "event": None,
        "handoff": None,
    }
    body.update(over)
    return body


def test_monitor_aggregates_without_identifiers_or_text() -> None:
    records = [
        _record("a", "understand", latency_ms=10.0),
        _record("a", "turn", latency_ms=120.0),
        _record("b", "understand", route="fallback"),
        _record("b", "turn", latency_ms=200.0, handoff={"reference": "T-1"}),
        _record("c", "understand", outcome="timeout"),
        _record("c", "escalate"),
        _record("c", "turn", outcome="failed", latency_ms=300.0),
        # A country outside MX, CO and AR is reported apart, not dropped.
        _record("x", "turn", country="PE", language="es-419", latency_ms=50.0),
        _record("x", "understand", country="PE", language="es-419"),
    ]
    summary = summarize(records, source="var/turns.jsonl", simulated=True)
    assert summary["workload"]["turns"] == 4
    assert summary["workload"]["records"] == 9
    assert summary["workload"]["simulated"] is True
    assert summary["workload"]["period"]["first"] == "2026-10-02T10:00:00+00:00"
    mx = summary["groups"]["MX"]["es-419"]
    assert mx["n"] == 3
    assert mx["turn_latency_ms"]["p50"] == 200.0
    assert mx["failed_or_timed_out_steps"]["n"] == 2
    assert mx["escalations"]["n"] == 1
    assert mx["handoffs"]["n"] == 1
    assert mx["fallback_turns"]["n"] == 1
    assert summary["groups"]["other"]["es-419"]["n"] == 1
    dumped = json.dumps(summary, sort_keys=True)
    assert "trace-a" not in dumped
    assert "session-a" not in dumped
    report = render_report(summary)
    assert "trace-a" not in report
    assert "| other | es-419 | 1 |" in report


def test_second_monitor_freeze_refuses_overwrite(tmp_path) -> None:
    summary = summarize([], source="var/turns.jsonl", simulated=True)
    freeze_monitoring(tmp_path, "mon-v1", summary, "# report\n")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        freeze_monitoring(tmp_path, "mon-v1", summary, "# report\n")
