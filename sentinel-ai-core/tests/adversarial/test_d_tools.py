"""D. Tool failures.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_confirmation.py::test_three_failed_lookups_hand_off_without_case_number`
(D1: bounded retries, handoff without a case number).

This module adds the writes-read-back path, a Gold that raises, and a Gold that
knows nothing.
"""

import pytest

from .conftest import CUSTOMER, EmptyGold, RaisingGold, facts_travel_nowhere, login_as, session_memory

# --- blocked (verified) ---


@pytest.mark.attack("D3", "blocked_verified")
def test_gold_that_raises_degrades_to_a_safe_answer(logged_in) -> None:
    """D3. An exploding Gold must not leak internals or invent a charge."""
    logged_in.app.state.gold = RaisingGold(RuntimeError("gold exploded: /var/lib/secret"))
    response = logged_in.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] in ("error", "handoff", "clarification", "text")
    assert "gold exploded" not in response.text
    assert "/var/lib/secret" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.attack("D2", "blocked_verified")
def test_gold_that_knows_nothing_never_confirms(logged_in) -> None:
    """D2. A reference that resolves to nothing cannot produce a case."""
    logged_in.app.state.gold = EmptyGold()
    response = logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    assert response.status_code == 200
    assert response.json()["kind"] != "case_confirmation"
    assert facts_travel_nowhere(response.json())


@pytest.mark.attack("D5", "blocked_verified")
def test_failed_read_back_never_becomes_a_case_number(logged_in) -> None:
    """D5. The write happens, the read-back fails, the customer is not told "ok".

    blocked (verified): `case_confirmation` is emitted only after
    `lookup_dispute` returns the record (REQ-0005). The flow is driven with two
    structured selections — the first opens the confirm box, the second opens
    the dispute — so the failing read-back is actually reached.
    """
    logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    memory = session_memory(logged_in)
    memory.lookup_failures_left = 99

    response = logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    body = response.json()
    assert body["kind"] == "handoff"
    assert "case_id" not in body
    assert len(memory.by_key) == 1, "the dispute was written exactly once (idempotent)"
    assert memory.open_calls >= 1, "the write happened before the read-back failed"


# --- blocked in code: a slow read cannot hold the request -----------------


@pytest.mark.attack("D4", "blocked_verified")
def test_slow_gold_does_not_hang_the_request(logged_in, monkeypatch) -> None:
    """D4. A slow Gold read is a failed attempt and ends in a handoff.

    blocked (verified): `SessionBoundLookup` runs the read under
    `SENTINEL_GOLD_TIMEOUT_S`. Three timeouts hand off with no case number,
    inside the attempts' total budget.
    """
    import time

    budget = 0.05
    monkeypatch.setenv("SENTINEL_GOLD_TIMEOUT_S", str(budget))

    class SlowGold:
        def get(self, reference: str, customer_id: str):  # type: ignore[no-untyped-def]
            time.sleep(0.4)
            return None

        def list_for_customer(self, customer_id: str):  # type: ignore[no-untyped-def]
            time.sleep(0.4)
            return []

    logged_in.app.state.gold = SlowGold()
    start = time.monotonic()
    response = logged_in.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    elapsed = time.monotonic() - start
    body = response.json()
    assert response.status_code == 200
    assert body["kind"] == "handoff"
    assert "case_id" not in body
    assert elapsed < budget * 3 + 0.2
    records = logged_in.app.state.recorder.records_for(response.headers["X-Trace-Id"])
    assert sum(1 for record in records if record.outcome == "timeout") == 3


@pytest.mark.attack("D6", "blocked_verified")
def test_disputes_api_cannot_skip_the_confirmation(logged_in) -> None:
    """D6. A direct create without a preview, or after a refused preview, writes nothing."""
    assert logged_in.post("/api/v1/disputes", json={"reference": "TXN-1006"}).status_code == 409
    refused = logged_in.post("/api/v1/disputes/preview", json={"reference": "TXN-1003"}).json()
    assert refused["kind"] == "text"
    assert logged_in.post("/api/v1/disputes", json={"reference": "TXN-1003"}).status_code == 409
    assert session_memory(logged_in).open_calls == 0


@pytest.mark.attack("D7", "blocked_verified")
def test_a_new_session_cannot_open_a_duplicate_dispute(logged_in) -> None:
    """D7. One charge, one case, whichever session or entry point asks again."""
    logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    first = logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()
    assert first["kind"] == "case_confirmation"
    logged_in.post("/api/v1/auth/logout")
    login_as(logged_in, CUSTOMER)
    preview = logged_in.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"}).json()
    assert preview == {"kind": "text", "message_key": "already.disputed"}
    disputes = [row for row in logged_in.get("/api/v1/disputes").json() if row["kind"] == "dispute"]
    assert [row["case_id"] for row in disputes] == [first["case_id"]]
