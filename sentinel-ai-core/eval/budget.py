"""Spend cap for runs that make live calls (decision 018, design §6).

The cap wraps the live transport, inside the recorder, so recorded hits cost
nothing and never count. Before each live call it adds the estimated cost of
that call (the mean so far, or a first estimate) to the spend so far; if the
sum would pass the cap, the run stops. A run stopped by the cap is not frozen.
"""

from __future__ import annotations

from app.ai.transport import LLMResponse, ModelTransport

DEFAULT_CAP_USD = 0.45
# About 1,000 input and 50 output tokens on the strong route (decision 016).
FIRST_CALL_ESTIMATE_USD = 0.0004


class SpendCapReached(RuntimeError):
    """The next live call would pass the spend cap. Deliberately not ModelUnavailable,
    so no caller can mistake it for a single failed call and keep going."""


class CappedTransport:
    def __init__(
        self,
        live: ModelTransport,
        cap_usd: float = DEFAULT_CAP_USD,
        first_estimate_usd: float = FIRST_CALL_ESTIMATE_USD,
    ) -> None:
        self._live = live
        self.cap_usd = cap_usd
        self._first_estimate = first_estimate_usd
        self.spent_usd = 0.0
        self.calls = 0
        self.capped = False

    def next_estimate(self) -> float:
        return self.spent_usd / self.calls if self.calls else self._first_estimate

    def complete(self, *, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> LLMResponse:
        if self.spent_usd + self.next_estimate() > self.cap_usd:
            self.capped = True
            raise SpendCapReached(
                f"spend cap USD {self.cap_usd} reached after {self.calls} calls (USD {self.spent_usd:.6f})"
            )
        response = self._live.complete(model=model, messages=messages, temperature=temperature)
        self.calls += 1
        self.spent_usd += response.cost_usd
        return response

    def report(self) -> dict:
        return {
            "n": self.calls,
            "cap_usd": self.cap_usd,
            "spent_usd": round(self.spent_usd, 6),
            "capped": self.capped,
        }


def assert_freezable(spend: dict) -> None:
    if spend.get("capped"):
        raise SpendCapReached("this run was stopped by the spend cap; it is not frozen as a measurement")


__all__ = ["DEFAULT_CAP_USD", "CappedTransport", "SpendCapReached", "assert_freezable"]
