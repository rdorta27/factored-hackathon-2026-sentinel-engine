"""The trained baseline: split guards, reproducibility, and the ModelPort behaviour."""

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from app.ai.port import ModelPort, UnderstandKind
from eval import train
from eval.cases import load_dir, validate_case
from eval.trained import ANALYZER, NGRAM_RANGE, TrainedBaseline, _vectorizer, prepare, tfidf

PHRASES = {
    "charge": ["no reconozco este cargo", "me cobraron dos veces", "não reconheço essa cobrança", "cargo raro de ayer"],
    "missing": ["hola buenos días", "gracias por todo", "olá, tudo bem", "no entiendo nada"],
    "out_of_scope": ["quiero un préstamo", "cuál es mi saldo", "quero um cartão novo", "cambiar mi dirección"],
    "person": ["quiero hablar con una persona", "preciso de um atendente", "pásame con un asesor", "quero falar com alguém"],
    "status": ["cómo va mi disputa", "qual o status do meu caso", "en qué va mi reclamo", "novedades de mi caso"],
}


def _row(case_id: str, intent: str, text: str, split: str) -> dict:
    return {
        "id": case_id, "base_id": case_id, "locale": "es-419", "country": "MX", "turns": [text],
        "expected_intent": intent, "expected_outcome": "clarification", "split": split,
    }


def _write(directory: Path, held_out_id: str | None = None) -> Path:
    rows = []
    for intent, texts in PHRASES.items():
        for i, text in enumerate(texts):
            split = "validation" if i == 3 else "development"
            rows.append(_row(f"{intent}-{i}", intent, text, split))
    if held_out_id:
        rows.append(_row(held_out_id, "charge", "texto sellado", "held_out"))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "dev.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return directory


def _case(case_id: str, split: str):  # type: ignore[no-untyped-def]
    return validate_case(_row(case_id, "charge", "no reconozco este cargo", split), "test")


def test_training_refuses_a_held_out_case() -> None:
    with pytest.raises(train.HeldOutInTraining, match="ho-9"):
        train.fit_and_select([_case("dev-1", "development"), _case("ho-9", "held_out")], [])


def test_training_refuses_a_validation_case_as_training_data() -> None:
    with pytest.raises(train.HeldOutInTraining, match="val-1"):
        train.fit_and_select([_case("val-1", "validation")], [])


def test_tuning_refuses_a_held_out_case() -> None:
    with pytest.raises(train.HeldOutInTraining, match="ho-2"):
        train.fit_and_select([_case("dev-1", "development")], [_case("ho-2", "held_out")])


def test_build_stops_when_a_held_out_case_is_in_the_split_files(tmp_path: Path) -> None:
    cases_dir = _write(tmp_path / "cases", held_out_id="ho-77")
    development, validation = train._load_splits(cases_dir)
    assert all(c.id != "ho-77" for c in development + validation)


def test_real_case_folder_has_no_held_out_case() -> None:
    cases = load_dir(train.CASES_DIR)
    assert {c.split for c in cases} <= {"development", "validation"}


def test_build_is_reproducible(tmp_path: Path) -> None:
    cases_dir = _write(tmp_path / "cases")
    first, text_a = train.build("t", cases_dir)
    second, text_b = train.build("t", cases_dir)
    assert first == second and text_a == text_b
    assert first["model"]["regularization_c"] in train.C_GRID
    assert first["splits"]["development"]["n"] == 15 and first["splits"]["validation"]["n"] == 5


def test_freeze_and_verify_round_trip(tmp_path: Path) -> None:
    cases_dir = _write(tmp_path / "cases")
    root = tmp_path / "repo"
    train.train("t-1", cases_dir, root)
    assert train.verify("t-1", cases_dir, root) is True
    model_file = root / "evidence" / "evaluation-runs" / "t-1" / train.MODEL_FILE
    model_file.write_text(model_file.read_text(encoding="utf-8") + " ", encoding="utf-8")
    assert train.verify("t-1", cases_dir, root) is False


def test_freeze_refuses_to_overwrite(tmp_path: Path) -> None:
    cases_dir = _write(tmp_path / "cases")
    train.train("t-1", cases_dir, tmp_path / "repo")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        train.train("t-1", cases_dir, tmp_path / "repo")


def test_tfidf_matches_scikit_learn() -> None:
    texts = [prepare(t) for group in PHRASES.values() for t in group]
    reference = TfidfVectorizer(analyzer=ANALYZER, ngram_range=NGRAM_RANGE, strip_accents="unicode", lowercase=True)
    expected = reference.fit_transform(texts).toarray()
    vocabulary = {term: i for i, term in enumerate(sorted(reference.vocabulary_, key=reference.vocabulary_.get))}
    mine = tfidf(_vectorizer(vocabulary), reference.idf_, texts)
    assert np.allclose(mine, expected)


def test_trained_baseline_is_a_model_port(tmp_path: Path) -> None:
    cases_dir = _write(tmp_path / "cases")
    _, text = train.build("t", cases_dir)
    model: ModelPort = TrainedBaseline(json.loads(text))
    result = model.understand("quiero hablar con una persona", ["quiero hablar con una persona"])
    assert result.kind is UnderstandKind.PERSON
    assert result.subtype is None and result.reply_draft is None
    info = model.describe()
    assert (info.model, info.route) == ("trained-baseline", "trained")
    assert model.classify("hola buenos días") == "missing"


def test_prepare_masks_identifiers_before_lowering() -> None:
    assert "@" not in prepare("mi correo es Ana.Perez@example.com")
