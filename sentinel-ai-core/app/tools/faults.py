"""Fault-injection adapters, one per port (REQ-0021, REQ-0026).

Selected with ``SENTINEL_FAULT_*``, all off by default:

- ``SENTINEL_FAULT_MODEL``: ``timeout`` | ``error_5xx`` | ``invalid_json``
- ``SENTINEL_FAULT_GOLD``: ``slow`` | ``error``
- ``SENTINEL_FAULT_GOLD_DELAY_S``: seconds ``slow`` sleeps (default 5)
- ``SENTINEL_FAULT_STORE``: ``error``

The frozen fault run starts the app with these set and drives it over HTTP
with ``scripts/inject_faults.py``. Production never sets them: ``create_app``
logs a warning whenever one is active.
"""

from __future__ import annotations

import logging
import os
import time

from app.ai.port import ModelInfo, ModelPort, UnderstandResult
from app.ai.transport import InvalidReply, ModelUnavailable
from app.tools.gold import GoldRow, GoldTransactions

log = logging.getLogger("sentinel.faults")

MODEL_ENV = "SENTINEL_FAULT_MODEL"
GOLD_ENV = "SENTINEL_FAULT_GOLD"
GOLD_DELAY_ENV = "SENTINEL_FAULT_GOLD_DELAY_S"
STORE_ENV = "SENTINEL_FAULT_STORE"

MODEL_FAULTS = frozenset({"timeout", "error_5xx", "invalid_json"})
GOLD_FAULTS = frozenset({"slow", "error"})


class FaultModel:
    """A model that fails the way the transport fails, before any fallback."""

    def __init__(self, primary: ModelPort, fault: str) -> None:
        if fault not in MODEL_FAULTS:
            raise ValueError(f"unknown model fault: {fault}")
        self._primary = primary
        self._fault = fault

    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult:
        if self._fault == "timeout":
            raise ModelUnavailable("fault injection: model timeout")
        if self._fault == "error_5xx":
            raise ModelUnavailable("fault injection: model endpoint 503")
        raise InvalidReply("fault injection: invalid model JSON")

    def classify(self, message: str) -> str:
        return self._primary.classify(message)

    def describe(self) -> ModelInfo:
        return self._primary.describe()


class SlowGold:
    """A Gold store that answers after a delay, so reads time out."""

    def __init__(self, store: GoldTransactions, delay_s: float = 5.0) -> None:
        self._store = store
        self._delay_s = delay_s

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        time.sleep(self._delay_s)
        return self._store.get(reference, customer_id)

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        time.sleep(self._delay_s)
        return self._store.list_for_customer(customer_id)

    def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
        return getattr(self._store, name)


class FailingGold:
    """A Gold store that raises on every read."""

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        raise RuntimeError("fault injection: gold store error")

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        raise RuntimeError("fault injection: gold store error")


class FailingCaseStore:
    """A case repository that raises on write and reads nothing."""

    def __init__(self, repo) -> None:  # type: ignore[no-untyped-def]
        self._repo = repo

    def add(self, row) -> None:  # type: ignore[no-untyped-def]
        raise RuntimeError("fault injection: case store error")

    def by_key(self, key: str):  # type: ignore[no-untyped-def]
        return self._repo.by_key(key)

    def get(self, case_id: str):  # type: ignore[no-untyped-def]
        return self._repo.get(case_id)

    def for_customer(self, customer_id: str):  # type: ignore[no-untyped-def]
        return self._repo.for_customer(customer_id)

    def set_reason(self, case_id: str, reason: str) -> None:
        raise RuntimeError("fault injection: case store error")

    def handoffs(self):  # type: ignore[no-untyped-def]
        return self._repo.handoffs()


def _gold_delay_s() -> float:
    try:
        return float(os.environ.get(GOLD_DELAY_ENV, "5.0"))
    except ValueError:
        return 5.0


def apply_model_fault(model: ModelPort) -> ModelPort:
    fault = os.environ.get(MODEL_ENV, "").strip().lower()
    if not fault:
        return model
    wrapped = FaultModel(model, fault)
    log.warning("fault injection active: model=%s", fault)
    return wrapped


def apply_gold_fault(gold: GoldTransactions) -> GoldTransactions:
    fault = os.environ.get(GOLD_ENV, "").strip().lower()
    if not fault:
        return gold
    if fault not in GOLD_FAULTS:
        raise ValueError(f"unknown gold fault: {fault}")
    wrapped: GoldTransactions = SlowGold(gold, _gold_delay_s()) if fault == "slow" else FailingGold()
    log.warning("fault injection active: gold=%s", fault)
    return wrapped


def apply_store_fault(repo):  # type: ignore[no-untyped-def]
    fault = os.environ.get(STORE_ENV, "").strip().lower()
    if not fault:
        return repo
    if fault != "error":
        raise ValueError(f"unknown store fault: {fault}")
    log.warning("fault injection active: store=%s", fault)
    return FailingCaseStore(repo)
