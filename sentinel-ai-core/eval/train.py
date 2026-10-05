"""Train the trained baseline on development, tune on validation, freeze the run.

Usage from ``sentinel-ai-core/``::

    python3 -m eval.run train 2024Q4-train-v1
    python3 -m eval.run verify 2024Q4-train-v1

Training reads the ``development`` split. The regularization parameter is the one
with the best ``validation`` accuracy. A case from any other split stops training
with an error that names the case. The sealed folder is never opened: the cases
come from ``eval/cases/*.jsonl`` only (decision 007, 2026-10-05 amendment).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from eval import metrics
from eval.cases import INTENTS, Case, check_splits, load_dir
from eval.report import EVAL_VERSION, freeze_run
from eval.trained import ANALYZER, DECIMALS, NGRAM_RANGE, TrainedBaseline, prepare

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
CASES_DIR = HERE / "cases"
MODEL_FILE = "model.json"
# Fixed before the first run. The best validation accuracy wins; a tie goes to the smaller C.
C_GRID = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0)
SEED = 0
MAX_ITER = 2000


class HeldOutInTraining(ValueError):
    """A case outside its split reached the training data."""


def assert_split(cases: list[Case], split: str, purpose: str) -> None:
    for case in cases:
        if case.split != split:
            raise HeldOutInTraining(f"case {case.id} has split {case.split!r}; {purpose} reads {split!r} only")


def _fit(texts: list[str], labels: list[str], c: float) -> tuple[TfidfVectorizer, LogisticRegression]:
    vectorizer = TfidfVectorizer(
        analyzer=ANALYZER, ngram_range=NGRAM_RANGE, strip_accents="unicode", lowercase=True
    )
    features = vectorizer.fit_transform(texts)
    model = LogisticRegression(C=c, max_iter=MAX_ITER, random_state=SEED)
    model.fit(features, labels)
    return vectorizer, model


def _body(vectorizer: TfidfVectorizer, model: LogisticRegression, c: float) -> dict:
    def rounded(values: np.ndarray) -> list:
        return np.round(values, DECIMALS).tolist()

    terms = sorted(vectorizer.vocabulary_, key=vectorizer.vocabulary_.get)  # type: ignore[arg-type]
    return {
        "analyzer": ANALYZER,
        "ngram_range": list(NGRAM_RANGE),
        "strip_accents": "unicode",
        "labels": [str(label) for label in model.classes_],
        "vocabulary": terms,
        "idf": rounded(vectorizer.idf_),
        "coef": rounded(model.coef_),
        "intercept": rounded(model.intercept_),
        "regularization_c": c,
        "seed": SEED,
        "sklearn_version": sklearn.__version__,
    }


def _serialize(body: dict) -> str:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"


def _score(model: TrainedBaseline, cases: list[Case]) -> dict:
    predicted = model.predict([c.message for c in cases])
    pairs = [(c.expected_intent, p) for c, p in zip(cases, predicted)]
    return metrics.intent_metrics(pairs, labels=list(INTENTS))


def fit_and_select(development: list[Case], validation: list[Case]) -> tuple[dict, dict]:
    """Return the model body of the best C and the validation table of every C."""
    assert_split(development, "development", "training")
    assert_split(validation, "validation", "tuning")
    texts = [prepare(c.message) for c in development]
    labels = [c.expected_intent for c in development]
    table: dict[str, float] = {}
    best: tuple[float, dict] | None = None
    for c in C_GRID:
        vectorizer, model = _fit(texts, labels, c)
        body = _body(vectorizer, model, c)
        accuracy = _score(TrainedBaseline(body), validation)["accuracy"]
        table[str(c)] = accuracy
        if best is None or accuracy > best[0]:
            best = (accuracy, body)
    assert best is not None
    return best[1], table


def _load_splits(cases_dir: Path) -> tuple[list[Case], list[Case]]:
    cases = load_dir(cases_dir)
    check_splits(cases)
    return (
        [c for c in cases if c.split == "development"],
        [c for c in cases if c.split == "validation"],
    )


def build(run_id: str, cases_dir: Path | str = CASES_DIR) -> tuple[dict, str]:
    """Train and return the summary and the model file text. Writes nothing."""
    development, validation = _load_splits(Path(cases_dir))
    body, table = fit_and_select(development, validation)
    text = _serialize(body)
    model = TrainedBaseline(body)
    unseen = [label for label in INTENTS if label not in {c.expected_intent for c in validation}]
    summary = {
        "run_id": run_id,
        "kind": "training",
        "eval_version": EVAL_VERSION,
        "model": {
            "name": "trained_baseline",
            "type": "tfidf_char_ngrams_logistic_regression",
            "analyzer": ANALYZER,
            "ngram_range": list(NGRAM_RANGE),
            "strip_accents": "unicode",
            "input": "masked and lower-cased first message",
            "labels": body["labels"],
            "features": len(body["vocabulary"]),
            "regularization_c": body["regularization_c"],
            "c_grid": list(C_GRID),
            "seed": SEED,
            "sklearn_version": sklearn.__version__,
            "file": MODEL_FILE,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        },
        "splits": {
            "development": {"n": len(development), "ids": [c.id for c in development]},
            "validation": {"n": len(validation), "ids": [c.id for c in validation]},
        },
        "validation": {
            "by_c": table,
            "selected": _score(model, validation),
        },
        "development_fit": _score(model, development),
        "notes": [
            "Team-written simulation cases, never dataset rows (decision 007).",
            "Trained on development, tuned on validation. No held-out case was read.",
            "The validation scores describe only. The claim comes from the single sealed measurement of eval-v8.",
            "The development fit is a training score. Do not read it as performance.",
            *(
                [f"The validation split has no case for: {', '.join(unseen)}. Their scores are 0.0 by construction."]
                if unseen
                else []
            ),
        ],
    }
    return summary, text


def train(run_id: str, cases_dir: Path | str = CASES_DIR, repo_root: Path | str = REPO_ROOT) -> dict:
    summary, text = build(run_id, cases_dir)
    folder = freeze_run(repo_root, run_id, summary, render(summary))
    (folder / MODEL_FILE).write_text(text, encoding="utf-8")
    return summary


def verify(run_id: str, cases_dir: Path | str = CASES_DIR, repo_root: Path | str = REPO_ROOT) -> bool:
    """Train again on the frozen split ids and compare the summary and the model hash."""
    folder = Path(repo_root) / "evidence" / "evaluation-runs" / run_id
    frozen = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    if frozen["model"]["sklearn_version"] != sklearn.__version__:
        raise SystemExit(
            f"the run used scikit-learn {frozen['model']['sklearn_version']}; "
            f"this environment has {sklearn.__version__}. Install the pinned version."
        )
    summary, text = build(run_id, cases_dir)
    on_disk = (folder / MODEL_FILE).read_text(encoding="utf-8")
    return summary == frozen and text == on_disk


def render(summary: dict) -> str:
    model = summary["model"]
    selected = summary["validation"]["selected"]
    lines = [
        f"# Training run {summary['run_id']}",
        "",
        f"Trained baseline: {model['type']}, {model['features']} features, labels {', '.join(model['labels'])}.",
        f"Development n={summary['splits']['development']['n']}, validation n={summary['splits']['validation']['n']}.",
        f"Selected C={model['regularization_c']} · model sha256 `{model['sha256'][:16]}` · scikit-learn {model['sklearn_version']}.",
        "",
        "## Validation accuracy by C",
        "",
        "| C | Accuracy |",
        "|---|---|",
    ]
    lines += [f"| {c} | {accuracy} |" for c, accuracy in summary["validation"]["by_c"].items()]
    lines += ["", "## Validation per intent (descriptive)", "", "| Intent | n | Precision | Recall | F1 |", "|---|---|---|---|---|"]
    for label, row in selected["per_class"].items():
        lines.append(f"| {label} | {row['n']} | {row['precision']} | {row['recall']} | {row['f1']} |")
    lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


__all__ = ["HeldOutInTraining", "assert_split", "build", "fit_and_select", "train", "verify"]
