"""Provider-agnostic model transport with bounded retry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx


class ModelUnavailable(Exception):
    """The model call failed or timed out after bounded retries."""


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


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
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._max_retries = max(0, max_retries)
        self._price_in = price_in_per_1k
        self._price_out = price_out_per_1k

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
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
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
                cost = (tokens_in * self._price_in + tokens_out * self._price_out) / 1000.0
                return LLMResponse(
                    content=str(content),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=cost,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                continue
        raise ModelUnavailable(str(last_error) if last_error else "model unavailable")
