from app.ai.port import UnderstandKind, UnderstandResult
from app.orchestrator.types import Language


class FakeModel:
    def __init__(self) -> None:
        self.classify_calls = 0
        self.scripts: dict[str, UnderstandResult] = {
            "no reconozco este cargo": UnderstandResult(
                UnderstandKind.CHARGE, Language.ES_419
            ),
            "não reconheço esta cobrança": UnderstandResult(
                UnderstandKind.CHARGE, Language.PT_BR
            ),
            "me cobraron dos veces": UnderstandResult(
                UnderstandKind.CHARGE, Language.ES_419
            ),
            "hay un problema": UnderstandResult(
                UnderstandKind.MISSING, Language.ES_419
            ),
            "tem um problema": UnderstandResult(
                UnderstandKind.MISSING, Language.PT_BR
            ),
            "cuál es mi saldo": UnderstandResult(
                UnderstandKind.OUT_OF_SCOPE, Language.ES_419
            ),
            "qual é o meu saldo": UnderstandResult(
                UnderstandKind.OUT_OF_SCOPE, Language.PT_BR
            ),
            "quiero una persona": UnderstandResult(
                UnderstandKind.PERSON, Language.ES_419
            ),
            "quero uma pessoa": UnderstandResult(
                UnderstandKind.PERSON, Language.PT_BR
            ),
        }
        self.categories = {
            "no reconozco este cargo": "Cargo no reconocido",
            "não reconheço esta cobrança": "Cargo no reconocido",
            "me cobraron dos veces": "Cargo duplicado",
        }

    def understand(self, message: str, turns: list[str]) -> UnderstandResult:
        if message in self.scripts:
            return self.scripts[message]
        for key, result in sorted(self.scripts.items(), key=lambda item: len(item[0]), reverse=True):
            if key in message:
                return result
        raise KeyError(message)

    def classify(self, message: str) -> str:
        self.classify_calls += 1
        if message in self.categories:
            return self.categories[message]
        for key, category in self.categories.items():
            if key in message:
                return category
        raise KeyError(message)
