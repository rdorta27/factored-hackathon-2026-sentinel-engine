"""Model selection for the served app: router_v2 from the environment, baseline otherwise.

The served configuration must equal the one measured in eval-v7 (decisions
016 and 018): one model on both routes, prompt v2 with the development
examples, reasoning effort ``low``, a 400-token cap, temperature 0. Unset
values fall back to those, so setting only the endpoint, the key and the
model names serves what was measured.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

from app.ai.demo import DemoModel
from app.ai.llm import Example, PromptedLLMRouter, RouterConfig
from app.ai.port import ModelInfo, ModelPort, UnderstandResult
from app.ai.prices import PRICES
from app.ai.transport import HttpTransport, ModelTransport, ModelUnavailable

log = logging.getLogger("sentinel.model")

PROMPT_WITH_EXAMPLES = "v2"
EXAMPLES_PATH = Path(__file__).resolve().parents[2] / "eval" / "examples_v2.json"
CASES_DIR = EXAMPLES_PATH.parent / "cases"

# Worst case per model call is timeout x (retries + 1). One model failure ends
# the turn on the baseline, so the loop's own retries never multiply it.
DEFAULT_TIMEOUT_S = 6.0
DEFAULT_MAX_RETRIES = 1
DEFAULT_MAX_TOKENS = 400
DEFAULT_REASONING_EFFORT = "low"


class FallbackModel:
    """Answer with the primary model; on ModelUnavailable answer the turn with the fallback."""

    def __init__(self, primary: ModelPort, fallback: ModelPort) -> None:
        self._primary = primary
        self._fallback = fallback
        # Per thread, like the router: the answer of this request's last call.
        self._state = threading.local()

    def describe(self) -> ModelInfo:
        last = getattr(self._state, "last", self._primary)
        info = last.describe()
        if last is self._fallback:
            return ModelInfo(model=info.model, route="fallback", prompt_version=info.prompt_version)
        return info

    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult:
        try:
            result = self._primary.understand(message, turns, context=context)
        except ModelUnavailable as exc:
            # Class and message only: the transport never puts the key in either.
            log.warning("model unavailable, baseline answers this turn: %s: %s", type(exc).__name__, exc)
            self._state.last = self._fallback
            return self._fallback.understand(message, turns, context=context)
        self._state.last = self._primary
        return result

    def classify(self, message: str) -> str:
        return self._primary.classify(message)


def load_examples() -> tuple[Example, ...]:
    """The v2 examples, built by the same loader as the eval; fail rather than serve another v2."""
    from eval.cases import load_dir
    from eval.examples import build_examples

    try:
        ids = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["ids"]
        examples = build_examples(load_dir(CASES_DIR), ids)
    except (OSError, KeyError, ValueError) as exc:
        raise RuntimeError(f"prompt v2 needs its development examples: {exc}") from exc
    if not examples:
        raise RuntimeError("prompt v2 needs its development examples: the list is empty")
    return examples


def router_config() -> RouterConfig:
    config = RouterConfig.from_env()
    if config.prompt_version == PROMPT_WITH_EXAMPLES:
        config.examples = load_examples()
    return config


def model_from_env(transport: ModelTransport | None = None) -> ModelPort:
    """Baseline unless SENTINEL_LLM_BASE_URL and SENTINEL_LLM_API_KEY are both set."""
    base_url = os.environ.get("SENTINEL_LLM_BASE_URL", "").strip()
    api_key = os.environ.get("SENTINEL_LLM_API_KEY", "").strip()
    if not base_url or not api_key:
        return DemoModel()
    config = router_config()
    if transport is None:
        transport = HttpTransport(
            base_url=base_url,
            api_key=api_key,
            timeout_s=float(os.environ.get("SENTINEL_LLM_TIMEOUT_S") or DEFAULT_TIMEOUT_S),
            max_retries=int(os.environ.get("SENTINEL_LLM_MAX_RETRIES") or DEFAULT_MAX_RETRIES),
            prices=PRICES,
            max_tokens=int(os.environ.get("SENTINEL_LLM_MAX_TOKENS") or DEFAULT_MAX_TOKENS),
            reasoning_effort=os.environ.get("SENTINEL_LLM_REASONING_EFFORT") or DEFAULT_REASONING_EFFORT,
        )
    return FallbackModel(PromptedLLMRouter(transport, config), DemoModel())
