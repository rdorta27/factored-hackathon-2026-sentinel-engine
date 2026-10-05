"""The trained baseline: TF-IDF on character n-grams and a logistic regression.

The frozen model is a JSON file with the vocabulary, the idf weights and the
coefficients, rounded to a fixed number of decimals. The file has no pickle and
no dataset row. Prediction uses public scikit-learn calls only. The service
never loads this module (decision 007, 2026-10-05 amendment).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from app.ai.port import ModelInfo, UnderstandKind, UnderstandResult
from app.orchestrator.types import Language
from app.privacy.mask import mask

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
# The frozen training run the runner loads (decision 013). A new run id means new evidence.
TRAIN_RUN = "2024Q4-train-v1"
MODEL_NAME = "trained-baseline"
ROUTE = "trained"
PROMPT_VERSION = "tfidf-lr"
DECIMALS = 6
ANALYZER = "char_wb"
NGRAM_RANGE = (3, 5)
_PT_MARKS = re.compile(r"[ãõç]|\b(você|não|obrigad[oa]|cobrança|fatura)\b")


def prepare(text: str) -> str:
    """Mask identifiers, then lower-case: the same input the router reads."""
    return mask(text).lower()


def _vectorizer(vocabulary: dict[str, int] | None = None) -> CountVectorizer:
    return CountVectorizer(
        analyzer=ANALYZER,
        ngram_range=NGRAM_RANGE,
        strip_accents="unicode",
        lowercase=True,
        vocabulary=vocabulary,
    )


def tfidf(vectorizer: CountVectorizer, idf: np.ndarray, texts: list[str]) -> np.ndarray:
    """Counts times idf, rows normalized to unit length (scikit-learn default)."""
    matrix = vectorizer.transform(texts).toarray().astype(float) * idf
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


class TrainedBaseline:
    """Behind ``ModelPort``: predicts the intent only. No subtype, no slots, no draft."""

    def __init__(self, body: dict) -> None:
        self.body = body
        self._labels: list[str] = list(body["labels"])
        self._idf = np.array(body["idf"], dtype=float)
        self._coef = np.array(body["coef"], dtype=float)
        self._intercept = np.array(body["intercept"], dtype=float)
        self._vectorizer = _vectorizer({term: i for i, term in enumerate(body["vocabulary"])})

    @classmethod
    def load(cls, path: Path | str) -> TrainedBaseline:
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def describe(self) -> ModelInfo:
        return ModelInfo(model=MODEL_NAME, route=ROUTE, prompt_version=PROMPT_VERSION)

    def predict(self, texts: list[str]) -> list[str]:
        features = tfidf(self._vectorizer, self._idf, [prepare(t) for t in texts])
        scores = features @ self._coef.T + self._intercept
        if len(self._labels) == 2:
            return [self._labels[int(s > 0)] for s in scores[:, 0]]
        return [self._labels[int(i)] for i in scores.argmax(axis=1)]

    def classify(self, message: str) -> str:
        return self.predict([message])[0]

    def understand(self, message: str, turns: list[str], context: dict | None = None) -> UnderstandResult:
        language = Language.PT_BR if _PT_MARKS.search(unicodedata.normalize("NFC", message.lower())) else Language.ES_419
        return UnderstandResult(kind=UnderstandKind(self.classify(message)), language=language)


def load_frozen(run_id: str = TRAIN_RUN, repo_root: Path | str = REPO_ROOT) -> TrainedBaseline:
    """Load the model file of a frozen training run. The file must match the frozen hash."""
    folder = Path(repo_root) / "evidence" / "evaluation-runs" / run_id
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    raw = (folder / summary["model"]["file"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != summary["model"]["sha256"]:
        raise ValueError(f"the model file of {run_id} does not match its frozen hash")
    return TrainedBaseline(json.loads(raw))


def trained_version(run_id: str = TRAIN_RUN, repo_root: Path | str = REPO_ROOT):  # type: ignore[no-untyped-def]
    """The ``trained_baseline`` entry for ``run_versions``. No model key, no cost, no transport."""
    from eval.versions import Version

    return Version(load_frozen(run_id, repo_root))


__all__ = ["DECIMALS", "MODEL_NAME", "TRAIN_RUN", "TrainedBaseline", "load_frozen", "prepare", "tfidf", "trained_version"]
