"""Train the charge selector and freeze the model (run train-v1).

Order of use of the data (decision 025):
1. Fit the weights on the train split only.
2. Calibrate the temperature on the train split only.
3. Set the picking threshold on the validation split only.
The test split is never read here. The run holds the weights file and aggregates.

    SENTINEL_GOLD_DUCKDB=<path> python -m eval.train_charge_ranker
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import date
from pathlib import Path

from app.ai import charge_ranker as ranker
from eval import charge_examples as gen
from eval.charge_pool import pool_candidates

ROOT = Path(__file__).resolve().parents[2] / "evidence" / "charge-ranker"
RUN = ROOT / "train-v1"
DATA_RUN = ROOT / "data-v1"
MAX_WRONG_PICKS = 0.01
PENALTIES = (1e-4, 1e-3, 1e-2)
EPOCHS = 300
SOURCES = (
    Path(__file__),
    Path(ranker.__file__),
    Path(gen.__file__),
    Path(__file__).with_name("charge_pool.py"),
)

Matrix = list[tuple[list[list[float]], int]]


def build_matrix(examples: list[gen.Example], rows: dict[str, list[gen.Row]]) -> Matrix:
    out: Matrix = []
    for item in examples:
        pool = pool_candidates(item, rows)
        features = ranker.feature_matrix(item.text, pool, date.fromisoformat(item.today))
        label = next(i for i, row in enumerate(pool) if row.candidate_id == item.target_id)
        out.append((features, label))
    return out


def _softmax(scores: list[float]) -> list[float]:
    peak = max(scores)
    weights = [math.exp(score - peak) for score in scores]
    total = sum(weights)
    return [weight / total for weight in weights]


def fit(matrix: Matrix, penalty: float, epochs: int = EPOCHS) -> list[float]:
    """Listwise logistic regression: each example is one softmax over its charges. Adam steps."""
    size = len(ranker.FEATURES)
    weights = [0.0] * size
    first = [0.0] * size
    second = [0.0] * size
    rate, beta1, beta2 = 0.05, 0.9, 0.999
    for step in range(1, epochs + 1):
        grad = [penalty * w for w in weights]
        for rows, label in matrix:
            probs = _softmax([sum(w * x for w, x in zip(weights, row)) for row in rows])
            for index, row in enumerate(rows):
                delta = (probs[index] - (index == label)) / len(matrix)
                if delta:
                    for k, value in enumerate(row):
                        if value:
                            grad[k] += delta * value
        for k in range(size):
            first[k] = beta1 * first[k] + (1 - beta1) * grad[k]
            second[k] = beta2 * second[k] + (1 - beta2) * grad[k] ** 2
            weights[k] -= rate * (first[k] / (1 - beta1**step)) / (math.sqrt(second[k] / (1 - beta2**step)) + 1e-8)
    return weights


def nll(matrix: Matrix, weights: list[float], temperature: float = 1.0) -> float:
    total = 0.0
    for rows, label in matrix:
        probs = _softmax([sum(w * x for w, x in zip(weights, row)) / temperature for row in rows])
        total -= math.log(max(probs[label], 1e-12))
    return total / len(matrix)


def top_picks(matrix: Matrix, weights: list[float], temperature: float) -> list[tuple[float, bool]]:
    out = []
    for rows, label in matrix:
        scores = [sum(w * x for w, x in zip(weights, row)) for row in rows]
        best = max(range(len(scores)), key=lambda i: scores[i])
        out.append((ranker.softmax_top(scores, temperature), best == label))
    return out


def calibrate(matrix: Matrix, weights: list[float]) -> float:
    """The temperature that gives the best log-loss for "the top charge is right", on train."""
    best, best_loss = 1.0, float("inf")
    for temperature in [0.5 + 0.05 * step for step in range(0, 51)]:
        loss = 0.0
        for confidence, right in top_picks(matrix, weights, temperature):
            confidence = min(max(confidence, 1e-9), 1 - 1e-9)
            loss -= math.log(confidence if right else 1 - confidence)
        if loss < best_loss:
            best, best_loss = temperature, loss
    return round(best, 2)


def choose_threshold(picks: list[tuple[float, bool]]) -> dict:
    """The lowest threshold with at most 1% wrong automatic picks over all examples."""
    total = len(picks)
    for threshold in sorted({round(conf, 6) for conf, _ in picks}):
        auto = [(conf, right) for conf, right in picks if conf >= threshold]
        wrong = sum(1 for _, right in auto if not right)
        if wrong / total <= MAX_WRONG_PICKS:
            return {
                "threshold": threshold, "automatic_picks": len(auto) / total, "wrong_automatic_picks": wrong / total,
            }
    return {"threshold": 1.01, "automatic_picks": 0.0, "wrong_automatic_picks": 0.0}


def main() -> None:
    if RUN.exists():
        raise SystemExit(f"{RUN} exists. A run is write-once: use a new folder name.")
    frozen = json.loads((DATA_RUN / "summary.json").read_text(encoding="utf-8"))["examples_hash"]
    examples, rows = gen.build_dataset(gen.gold_path())
    if gen.digest_of(examples) != frozen:
        raise SystemExit("The rebuilt examples differ from the frozen run data-v1.")
    train = build_matrix([i for i in examples if i.split == "train"], rows)
    validation = build_matrix([i for i in examples if i.split == "validation"], rows)

    tried = {}
    for penalty in PENALTIES:
        weights = fit(train, penalty)
        tried[penalty] = (nll(validation, weights), weights)
        print(f"penalty {penalty}: validation log-loss {tried[penalty][0]:.4f}", file=sys.stderr)
    penalty = min(tried, key=lambda key: tried[key][0])
    weights = tried[penalty][1]
    temperature = calibrate(train, weights)
    chosen = choose_threshold(top_picks(validation, weights, temperature))

    RUN.mkdir(parents=True)
    model = {
        "features": list(ranker.FEATURES),
        "weights": [round(w, 6) for w in weights],
        "temperature": temperature,
        "threshold": chosen["threshold"],
    }
    model_path = RUN / "model.json"
    model_path.write_text(json.dumps(model, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    right_first = lambda matrix: sum(  # noqa: E731
        1 for rows, label in matrix
        if max(range(len(rows)), key=lambda i: sum(w * x for w, x in zip(weights, rows[i]))) == label
    ) / len(matrix)
    summary = {
        "run": "charge-ranker/train-v1",
        "data_type": "Simulation: weights fitted on team-generated descriptions of real Gold transactions.",
        "data_run": "charge-ranker/data-v1",
        "examples_hash": frozen,
        "seed": gen.SEED,
        "families_seen_in_training": list(gen.TRAIN_FAMILIES),
        "model_sha256": ranker.file_hash(model_path),
        "code_hash": hashlib.sha256(b"".join(path.read_bytes() for path in SOURCES)).hexdigest(),
        "penalty": penalty,
        "penalties_tried": {str(key): round(value[0], 6) for key, value in tried.items()},
        "temperature": temperature,
        "threshold": chosen["threshold"],
        "train": {"examples": len(train), "right_charge_first": right_first(train), "log_loss": nll(train, weights)},
        "validation": {
            "examples": len(validation),
            "right_charge_first": right_first(validation),
            "automatic_picks": chosen["automatic_picks"],
            "wrong_automatic_picks": chosen["wrong_automatic_picks"],
            "max_wrong_automatic_picks": MAX_WRONG_PICKS,
        },
        "test_split_read": False,
    }
    (RUN / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
