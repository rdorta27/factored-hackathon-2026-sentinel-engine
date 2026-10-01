"""Prompted LLM router behind ModelPort with Gold-aligned, PII-free requests."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from app.ai.port import ModelInfo, UnderstandKind, UnderstandResult
from app.ai.transport import ModelTransport, ModelUnavailable
from app.orchestrator.types import Language

PROMPT_VERSION_DEFAULT = "v1"

# Cheap heuristic used only to pick the route before the model call.
_PT_MARKS = ("não", "nao", "cobrança", "cobranca", "pessoa", "junho", "qual é", "quero", "obrigado")

# Keys that must never leave the process inside a model request.
FORBIDDEN_KEYS = frozenset(
    {
        "customer_id",
        "session_token",
        "session_ref",
        "customer_first_name",
        "customer_last_name",
        "customer_credit_score",
        "first_name",
        "last_name",
        "document_number",
        "document_type",
        "date_of_birth",
        "credit_score",
    }
)

# Charge fields the model may see, named as in ServiceDisputeEligibleTransaction
# with a numeric amount. No name, document or credit score, and no fraud_score:
# the policy engine reads the score from Gold; the model never needs it.
ALLOWED_CHARGE_KEYS = frozenset(
    {
        "transaction_id",
        "amount",
        "merchant_name",
        "merchant_category",
        "transaction_type",
        "currency",
        "channel",
        "transaction_country",
        "transaction_status",
    }
)

SYSTEM_PROMPT = (
    "You route a bank dispute intake turn. Reply with JSON only: "
    '{"intent": "charge|missing|out_of_scope|person", "language": "es-419|pt-BR", '
    '"amount": number|null}. '
    "Use ServiceDisputeEligibleTransaction field names with a numeric amount. "
    "Never ask for or repeat personal data."
)


def pick_route(message: str) -> str:
    text = message.lower()
    if any(mark in text for mark in _PT_MARKS):
        return "strong"
    if len(message) > 120:
        return "strong"
    return "cheap"


def assert_no_forbidden(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                raise ValueError(f"forbidden key in model request: {key}")
            assert_no_forbidden(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            assert_no_forbidden(item)


def build_messages(
    message: str, turns: list[str], charge: dict | None = None
) -> list[dict[str, str]]:
    window = [turn for turn in turns[-4:] if isinstance(turn, str)][:4]
    user_body: dict = {"message": message, "turns": window}
    if charge:
        unknown = set(charge) - ALLOWED_CHARGE_KEYS
        if unknown:
            raise ValueError(f"charge field not allowed in model request: {sorted(unknown)}")
        amount = charge.get("amount", None)
        if amount is not None and not isinstance(amount, (int, float)):
            raise ValueError("charge amount must be numeric")
        user_body["charge"] = {key: charge[key] for key in sorted(charge)}
    assert_no_forbidden(user_body)
    content = json.dumps(user_body, ensure_ascii=False)
    assert_no_forbidden({"content": content} if False else user_body)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def parse_content(content: str) -> tuple[UnderstandKind, Language]:
    try:
        body = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelUnavailable(f"unparsable model reply: {exc}") from exc
    intent = str(body.get("intent", "")).lower()
    language = str(body.get("language", ""))
    kinds = {
        "charge": UnderstandKind.CHARGE,
        "missing": UnderstandKind.MISSING,
        "out_of_scope": UnderstandKind.OUT_OF_SCOPE,
        "person": UnderstandKind.PERSON,
    }
    if intent not in kinds:
        raise ModelUnavailable(f"unknown intent: {intent!r}")
    if language == "pt-BR":
        lang = Language.PT_BR
    elif language in ("es-419", "es"):
        lang = Language.ES_419
    else:
        raise ModelUnavailable(f"unknown language: {language!r}")
    return kinds[intent], lang


@dataclass
class RouterConfig:
    cheap_model: str = ""
    strong_model: str = ""
    default_model: str = ""
    prompt_version: str = PROMPT_VERSION_DEFAULT
    temperature: float = 0.0

    @classmethod
    def from_env(cls) -> RouterConfig:
        return cls(
            cheap_model=os.environ.get("SENTINEL_LLM_CHEAP_MODEL", ""),
            strong_model=os.environ.get("SENTINEL_LLM_STRONG_MODEL", ""),
            default_model=os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", ""),
            prompt_version=os.environ.get("SENTINEL_LLM_PROMPT_VERSION", PROMPT_VERSION_DEFAULT)
            or PROMPT_VERSION_DEFAULT,
        )


class PromptedLLMRouter:
    """Route each understand call to a model without changing loop outcomes."""

    def __init__(self, transport: ModelTransport, config: RouterConfig) -> None:
        self._transport = transport
        self._config = config
        fallback = config.default_model or config.cheap_model or config.strong_model or "default"
        self._last_model = fallback
        self._last_route = "default"

    def describe(self) -> ModelInfo:
        return ModelInfo(
            model=self._last_model,
            route=self._last_route,
            prompt_version=self._config.prompt_version,
        )

    def _model_for(self, route: str) -> str:
        table = {"cheap": self._config.cheap_model, "strong": self._config.strong_model}
        chosen = (table.get(route) or "").strip()
        if chosen:
            return chosen
        fallback = (self._config.default_model or self._config.cheap_model or "").strip()
        return fallback or "default"

    def understand(self, message: str, turns: list[str]) -> UnderstandResult:
        route = pick_route(message)
        model = self._model_for(route)
        messages = build_messages(message, turns)
        response = self._transport.complete(
            model=model, messages=messages, temperature=self._config.temperature
        )
        kind, language = parse_content(response.content)
        self._last_route = route
        self._last_model = model
        return UnderstandResult(
            kind=kind,
            language=language,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            cost_usd=response.cost_usd,
        )

    def classify(self, message: str) -> str:
        text = message.lower()
        if "dos veces" in text or "duas vezes" in text or "duplic" in text:
            return "Cargo duplicado"
        return "Cargo no reconocido"
