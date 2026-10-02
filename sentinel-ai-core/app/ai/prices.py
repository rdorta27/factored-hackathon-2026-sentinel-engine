"""Per-model prices in USD per million tokens, copied from decision 016.

Source: Fireworks model library, read on 2026-10-01. DeepSeek V4.1 Flash is
listed under two ids; both carry the same price until the first live call
shows which one resolves.
"""

from __future__ import annotations

from dataclasses import dataclass

PRICE_SOURCE = "Fireworks model library, 2026-10-01 (decision 016)"


@dataclass(frozen=True)
class ModelPrice:
    input: float
    output: float
    cached_input: float | None = None


PRICES: dict[str, ModelPrice] = {
    "accounts/fireworks/models/gpt-oss-120b": ModelPrice(0.15, 0.60),
    "accounts/fireworks/models/glm-5p3-flash": ModelPrice(0.15, 0.50),
    "accounts/fireworks/models/deepseek-v4p1-flash": ModelPrice(0.30, 1.20, cached_input=0.006),
    "accounts/deepseek-ai/models/deepseek-v4p1-flash": ModelPrice(0.30, 1.20, cached_input=0.006),
    "accounts/fireworks/models/glm-5p3": ModelPrice(1.40, 4.40),
}


class UnknownPrice(KeyError):
    """A model has no declared price."""


def price_for(model: str, prices: dict[str, ModelPrice] | None = None) -> ModelPrice:
    table = PRICES if prices is None else prices
    if model not in table:
        raise UnknownPrice(f"no declared price for model {model!r}; add it to app/ai/prices.py from 016")
    return table[model]


def cost_usd(price: ModelPrice, tokens_in: int, tokens_out: int, cached_in: int = 0) -> float:
    cached = max(0, min(cached_in, tokens_in)) if price.cached_input is not None else 0
    fresh = tokens_in - cached
    total = fresh * price.input + cached * (price.cached_input or 0.0) + tokens_out * price.output
    return total / 1_000_000


__all__ = ["PRICES", "PRICE_SOURCE", "ModelPrice", "UnknownPrice", "cost_usd", "price_for"]
