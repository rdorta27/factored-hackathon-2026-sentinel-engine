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
from app.ai.llm import Cutoffs, Example, PromptedLLMRouter, RouterConfig
from app.ai.port import ModelInfo, ModelPort, UnderstandResult
from app.ai.prices import PRICES
from app.ai.transport import HttpTransport, ModelTransport, ModelUnavailable

log = logging.getLogger("sentinel.model")

PROMPT_WITH_EXAMPLES = "v2"
# A copy of the eval examples, so the image needs neither eval/ nor the case files
# (and never ships the sealed held-out set). A test keeps it equal to the eval loader.
EXAMPLES_PATH = Path(__file__).resolve().parent / "examples_v2.json"
# The calibrated cut-offs, next to the examples, with the run that chose them
# (018 amendment). Loaded only when the setting below is on.
CUTOFFS_PATH = Path(__file__).resolve().parent / "router_config.json"

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
    """The v2 examples measured in eval-v7; fail rather than serve another v2."""
    try:
        rows = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["examples"]
        examples = tuple(Example(case_id=row["case_id"], message=row["message"], reply=row["reply"]) for row in rows)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"prompt v2 needs its development examples: {exc}") from exc
    if not examples:
        raise RuntimeError("prompt v2 needs its development examples: the list is empty")
    return examples


def cutoffs_enabled() -> bool:
    """Off by default: without the setting the app serves v2 without cut-offs."""
    return os.environ.get("SENTINEL_LLM_CUTOFFS", "").strip().lower() in ("1", "true", "on", "yes")


def load_cutoffs() -> Cutoffs:
    """The calibrated cut-offs; fail rather than serve a partial configuration."""
    try:
        body = json.loads(CUTOFFS_PATH.read_text(encoding="utf-8"))
        return Cutoffs(
            t_act=float(body["t_act"]),
            t_abstain=float(body["t_abstain"]),
            calibration_run=str(body["calibration_run"]),
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"cut-offs need a valid router configuration: {exc}") from exc


def router_config() -> RouterConfig:
    config = RouterConfig.from_env()
    if config.prompt_version == PROMPT_WITH_EXAMPLES:
        config.examples = load_examples()
    if cutoffs_enabled():
        config.cutoffs = load_cutoffs()
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
