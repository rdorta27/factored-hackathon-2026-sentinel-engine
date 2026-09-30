"""D. Tool failures.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_confirmation.py::test_three_failed_lookups_hand_off_without_case_number`
(D1: bounded retries, handoff without a case number).

This module adds the writes-read-back path, a Gold that raises, and a Gold that
knows nothing.
"""

import pytest

from .conftest import EmptyGold, RaisingGold, facts_travel_nowhere

# --- blocked (verified) ---


def test_gold_that_raises_degrades_to_a_safe_answer(logged_in) -> None:
    """D3. An exploding Gold must not leak internals or invent a charge."""
    logged_in.app.state.gold = RaisingGold(RuntimeError("gold exploded: /var/lib/secret"))
    response = logged_in.post("/chat", json={"message": "no reconozco un cargo"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] in ("error", "handoff", "clarification", "text")
    assert "gold exploded" not in response.text
    assert "/var/lib/secret" not in response.text
    assert "Traceback" not in response.text


def test_gold_that_knows_nothing_never_confirms(logged_in) -> None:
    """D2. A reference that resolves to nothing cannot produce a case."""
    logged_in.app.state.gold = EmptyGold()
    response = logged_in.post("/chat", json={"selected_reference": "TXN-1001"})
    assert response.status_code == 200
    assert response.json()["kind"] != "case_confirmation"
    assert facts_travel_nowhere(response.json())


def test_failed_read_back_never_becomes_a_case_number(logged_in) -> None:
    """D5. The write happens, the read-back fails, the customer is not told "ok".

    blocked (verified): `case_confirmation` is emitted only after
    `lookup_dispute` returns the record (REQ-0005).
    """
    from app.tools.fake import InMemoryTools

    memories = logged_in.app.state.memories
    memory = memories.setdefault("CUST-0001", InMemoryTools())
    memory.lookup_failures_left = 99

    logged_in.post("/chat", json={"message": "no reconozco un cargo"})
    response = logged_in.post("/chat", json={"selected_reference": "TXN-1001"})
    body = response.json()
    assert body["kind"] != "case_confirmation"
    assert "case_id" not in body


# --- no defense yet ---


@pytest.mark.xfail(
    strict=True,
    reason="no HTTP client or tool timeout configured; the in-memory fake cannot time out",
)
def test_slow_gold_does_not_hang_the_request(logged_in) -> None:
    """D4. A latency budget needs a real client with a timeout.

    Simulating `sleep` in a fake would test the fake, not the failure handling
    of the tool call, so this stays unblocked until Gold is a real read.
    """
    import time

    class SlowGold:
        def get(self, reference: str, customer_id: str):  # type: ignore[no-untyped-def]
            time.sleep(30)
            return None

        def list_for_customer(self, customer_id: str):  # type: ignore[no-untyped-def]
            time.sleep(30)
            return []

    logged_in.app.state.gold = SlowGold()
    start = time.monotonic()
    response = logged_in.post("/chat", json={"message": "no reconozco un cargo"})
    elapsed = time.monotonic() - start
    assert response.status_code == 200
    assert elapsed < 5, "a slow tool must not hold the request open"
