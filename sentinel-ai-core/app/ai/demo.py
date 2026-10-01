from app.ai.port import ModelInfo, UnderstandKind, UnderstandResult
from app.orchestrator.types import Language

_PERSON = ("persona", "pessoa", "asesor", "atendente", "agente")
_OUT = ("saldo", "balance", "tarjeta", "cartao", "cartão", "credito", "crédito", "producto", "produto")
_PT = ("não", "nao", "cobrança", "cobranca", "pessoa", "junho", "qual é", "quero")
# An explicit "it was not me" claim. "No reconozco" alone is the normal dispute intent.
_NOT_MINE = (
    "no fui yo", "no lo hice yo", "no lo hice", "no la hice", "alguien usó mi", "alguien uso mi",
    "me clonaron", "clonaron mi", "no autoricé", "no autorice",
    "não fui eu", "nao fui eu", "alguém usou meu", "alguem usou meu", "clonaram", "não autorizei", "nao autorizei",
)


class DemoModel:
    def describe(self) -> ModelInfo:
        return ModelInfo(model="keyword-baseline", route="baseline", prompt_version="v1")

    def understand(self, message: str, turns: list[str]) -> UnderstandResult:
        text = message.lower()
        language = Language.PT_BR if any(mark in text for mark in _PT) else Language.ES_419
        if any(phrase in text for phrase in _NOT_MINE):
            return UnderstandResult(UnderstandKind.CHARGE, language, not_mine=True)
        if any(word in text for word in _PERSON):
            return UnderstandResult(UnderstandKind.PERSON, language)
        if any(word in text for word in _OUT):
            return UnderstandResult(UnderstandKind.OUT_OF_SCOPE, language)
        return UnderstandResult(UnderstandKind.CHARGE, language)

    def classify(self, message: str) -> str:
        text = message.lower()
        if "dos veces" in text or "duas vezes" in text or "duplic" in text:
            return "Cargo duplicado"
        return "Cargo no reconocido"
