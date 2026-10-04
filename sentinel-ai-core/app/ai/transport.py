"""Provider-agnostic model transport with bounded retry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.ai.prices import ModelPrice, UnknownPrice, cost_usd, price_for


class ModelUnavailable(Exception):
    """The model call failed or timed out after bounded retries."""


class InvalidReply(ModelUnavailable):
    """The model answered, but not with the JSON the router expects.

    A subclass of ModelUnavailable so the loop degrades the same way; the
    evaluation counts it separately as a JSON failure.
    """


@dataclass(frozen=True)
class TokenLogprob:
    """One content token and its alternatives, as the provider returns them.

    ``top`` holds (token, logprob) pairs in the provider's order, the chosen
    token included; an empty tuple when the provider sent no alternatives.
    """

    token: str
    logprob: float
    top: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    # Content-token log-probabilities when the provider returned them, else None.
    # Absent means the turn has no confidence and behaves as before (REQ-0016).
    logprobs: tuple[TokenLogprob, ...] | None = None


def parse_logprobs(raw: object) -> tuple[TokenLogprob, ...] | None:
    """Read ``choices[].logprobs.content`` into typed tokens; None when absent."""
    if not isinstance(raw, list) or not raw:
        return None
    parsed: list[TokenLogprob] = []
    for entry in raw:
        if not isinstance(entry, dict) or not isinstance(entry.get("token"), str):
            continue
        top = tuple(
            (str(alt["token"]), float(alt.get("logprob", 0.0) or 0.0))
            for alt in (entry.get("top_logprobs") or [])
            if isinstance(alt, dict) and isinstance(alt.get("token"), str)
        )
        parsed.append(
            TokenLogprob(
                token=str(entry["token"]),
                logprob=float(entry.get("logprob", 0.0) or 0.0),
                top=top,
            )
        )
    return tuple(parsed) or None


def logprobs_to_json(logprobs: tuple[TokenLogprob, ...] | None) -> list[dict] | None:
    """Serialize log-probabilities for a recording; None stays None."""
    if logprobs is None:
        return None
    return [
        {
            "token": entry.token,
            "logprob": entry.logprob,
            "top_logprobs": [{"token": token, "logprob": logprob} for token, logprob in entry.top],
        }
        for entry in logprobs
    ]


def logprobs_from_json(raw: object) -> tuple[TokenLogprob, ...] | None:
    """Rebuild log-probabilities from a recording body; None when absent."""
    return parse_logprobs(raw)


class ModelTransport(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse: ...


# Fallback per-1k-token prices when the route table carries none (USD).
_DEFAULT_PRICE_IN_PER_1K = 0.0015
_DEFAULT_PRICE_OUT_PER_1K = 0.002


class HttpTransport:
    """POST JSON to an OpenAI-compatible chat-completions endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout_s: float = 10.0,
        max_retries: int = 2,
        price_in_per_1k: float = _DEFAULT_PRICE_IN_PER_1K,
        price_out_per_1k: float = _DEFAULT_PRICE_OUT_PER_1K,
        prices: dict[str, ModelPrice] | None = None,
        require_price: bool = False,
        max_tokens: int | None = 200,
        json_mode: bool = True,
        reasoning_effort: str | None = None,
        logprobs: bool = True,
        top_logprobs: int = 5,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._max_retries = max(0, max_retries)
        self._price_in = price_in_per_1k
        self._price_out = price_out_per_1k
        # With a price table, cost follows the serving model; require_price makes
        # an unpriced model fail instead of falling back to the flat default.
        self._prices = prices
        self._require_price = require_price
        # Bounded JSON: the cap covers reasoning tokens too, which is what keeps
        # a reasoning model's cost near the estimate in decision 016.
        self._max_tokens = max_tokens
        self._json_mode = json_mode
        self._reasoning_effort = reasoning_effort
        # Ask for the label token's alternatives so the router can score its
        # label; a reply without them still works (confidence stays absent).
        self._logprobs = logprobs
        self._top_logprobs = top_logprobs

    def _cost(self, model: str, tokens_in: int, tokens_out: int, cached_in: int) -> float:
        if self._prices is not None or self._require_price:
            try:
                return cost_usd(price_for(model, self._prices), tokens_in, tokens_out, cached_in)
            except UnknownPrice:
                if self._require_price:
                    raise
        return (tokens_in * self._price_in + tokens_out * self._price_out) / 1000.0

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if self._max_tokens:
            payload["max_tokens"] = self._max_tokens
        if self._json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self._reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        if self._logprobs:
            payload["logprobs"] = True
            if self._top_logprobs > 0:
                payload["top_logprobs"] = self._top_logprobs
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        if self._require_price:
            price_for(model, self._prices)
        last_error: Exception | None = None
        for _ in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_s) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                if response.status_code >= 500:
                    last_error = ModelUnavailable(f"model endpoint {response.status_code}")
                    continue
                if response.status_code >= 400:
                    raise ModelUnavailable(f"model endpoint {response.status_code}")
                body = response.json()
                choice = (body.get("choices") or [{}])[0]
                content = ((choice.get("message") or {}).get("content")) or ""
                usage = body.get("usage") or {}
                tokens_in = int(usage.get("prompt_tokens", 0) or 0)
                tokens_out = int(usage.get("completion_tokens", 0) or 0)
                details = usage.get("prompt_tokens_details") or {}
                cached_in = int(details.get("cached_tokens", 0) or 0)
                cost = self._cost(model, tokens_in, tokens_out, cached_in)
                logprobs = parse_logprobs((choice.get("logprobs") or {}).get("content"))
                return LLMResponse(
                    content=str(content),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=cost,
                    logprobs=logprobs,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                continue
        raise ModelUnavailable(str(last_error) if last_error else "model unavailable")
