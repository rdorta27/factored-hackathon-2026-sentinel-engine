"""Strict Gold mode: refuse missing or stale Gold, start with the mock off."""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.tools.gold_strict import check

NOW = 1_700_000_000.0


def test_strict_mode_refuses_the_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    monkeypatch.setenv("SENTINEL_GOLD_REQUIRED", "1")
    with pytest.raises(RuntimeError, match="labelled mock"):
        create_app()


def test_strict_mode_off_starts_with_the_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    monkeypatch.delenv("SENTINEL_GOLD_REQUIRED", raising=False)
    body = TestClient(create_app()).get("/api/v1/health").json()
    assert (body["gold_source"], body["gold_required"]) == ("mock", "off")


def test_fresh_gold_passes() -> None:
    check("duckdb", NOW - 3600.0, NOW, 24.0)


def test_stale_gold_is_refused() -> None:
    with pytest.raises(RuntimeError, match="old"):
        check("duckdb", NOW - 48 * 3600.0, NOW, 24.0)


def test_missing_gold_files_are_refused() -> None:
    with pytest.raises(RuntimeError, match="no Gold file"):
        check("duckdb", None, NOW, 24.0)


def test_strict_mode_reports_on_in_health(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.tools.gold import MockGoldStore

    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    monkeypatch.setenv("SENTINEL_GOLD_REQUIRED", "true")
    monkeypatch.setattr("app.tools.gold_strict.gold_files_mtime", lambda: time.time())
    monkeypatch.setattr(
        "app.tools.gold_duckdb.select_gold",
        lambda as_of: (MockGoldStore(as_of=as_of), "duckdb"),
    )
    body = TestClient(create_app()).get("/api/v1/health").json()
    assert (body["gold_source"], body["gold_required"]) == ("duckdb", "on")
