"""Replay 50 development-window transcript openings through the chat.

The 70/30 cut is 2025-07-01: development is strictly before that date, held-out
is on or after it. Held-out rows are counted and dropped, never replayed.
Customer text, identifiers and the bucket name are not written. If the
transcript files are not on disk, the script stops and writes nothing.
"""

from __future__ import annotations

import csv
import glob
import json
import os
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HELD_OUT_CUT = "2025-07-01"
SAMPLE_RATE = 0.02
SEED = 20261002
DATE_KEYS = ("interaction_date", "process_date", "transcript_date")
_PART = re.compile(r"year=(\d{4}).*month=(\d{2}).*day=(\d{2})")


def event_date(row: dict, path: str) -> str | None:
    for key in DATE_KEYS:
        raw = (row.get(key) or "").strip()[:10]
        if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
            return raw
    match = _PART.search(path.replace("\\", "/"))
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def is_development(day: str) -> bool:
    return day < HELD_OUT_CUT


def search_roots() -> list[Path]:
    env = os.environ.get("SENTINEL_TRANSCRIPT_DIR")
    roots = [Path(env)] if env else []
    here = Path(__file__).resolve()
    repo = here.parents[2]
    roots.append(repo / "sentinel-data-engine" / "data")
    roots.append(repo / "evidence" / "flows" / "data")
    # Read-only working copy used by the flow measurements. Not copied into the repo.
    roots.append(repo.parent / "analisis" / "flujos" / "data")
    return roots


def source_label(path: str) -> str:
    normalized = path.replace("\\", "/")
    if "sentinel-data-engine/data" in normalized:
        return "sentinel-data-engine/data"
    if "/analisis/" in normalized:
        return "analysis-working-copy"
    return "local-data"


def transcript_files() -> list[str]:
    found: list[str] = []
    for root in search_roots():
        if not root.is_dir():
            continue
        found.extend(glob.glob(str(root / "**" / "*.csv"), recursive=True))
    return sorted(path for path in found if "transcript" in path.replace("\\", "/").lower())


def load_openings(files: list[str]) -> tuple[list[dict], int]:
    """Return development openings and the number of held-out rows excluded."""
    development: list[dict] = []
    held_out = 0
    for path in files:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                text = (row.get("customer_text") or "").strip()
                day = event_date(row, path)
                if not text or day is None:
                    continue
                if not is_development(day):
                    held_out += 1
                    continue
                development.append({"text": text, "date": day})
    return development, held_out


def sample_size(n_development: int, rate: float = SAMPLE_RATE) -> int:
    """One percent, at least one when any development opening exists."""
    if n_development <= 0:
        return 0
    return max(1, int(n_development * rate))


def take_sample(rows: list[dict], n: int | None = None, seed: int = SEED) -> list[dict]:
    wanted = sample_size(len(rows)) if n is None else n
    if len(rows) <= wanted:
        return list(rows)
    picker = random.Random(seed)
    return picker.sample(rows, wanted)


def replay_kinds(messages: list[str]) -> Counter:
    # Local HTTP replay. Production keeps the Secure cookie.
    os.environ.setdefault("SENTINEL_SECURE_COOKIES", "false")
    from fastapi.testclient import TestClient

    from app.main import create_app

    api = TestClient(create_app())
    assert api.post(
        "/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}
    ).status_code == 200
    kinds: Counter = Counter()
    for message in messages:
        response = api.post("/api/v1/chat", json={"message": message})
        kinds[response.json().get("kind", "error") if response.status_code == 200 else "http_error"] += 1
        api.post("/api/v1/auth/logout")
        assert api.post(
            "/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}
        ).status_code == 200
    return kinds


def summary(
    development: list[dict], held_out: int, sample: list[dict], kinds: Counter, source: str
) -> dict:
    prefixes = {(row["text"] or "")[:60] for row in sample}
    return {
        "split": "development",
        "source": source,
        "held_out_cut": HELD_OUT_CUT,
        "n_development": len(development),
        "n_held_out_excluded": held_out,
        "n_sampled": len(sample),
        "sample_rate": SAMPLE_RATE,
        "seed": SEED,
        "by_kind": dict(sorted(kinds.items())),
        "distinct_prefixes_in_sample": len(prefixes),
        "text_stored": False,
        "note": (
            "70/30 time split. Development is before the held-out cut 2025-07-01; "
            "held-out rows are excluded and not replayed. "
            "Transcript text is templated Spanish, not customer language. "
            "No customer data, identifiers or text are stored in the repo."
        ),
    }


def main() -> int:
    files = transcript_files()
    if not files:
        print("stopped: no transcript CSVs on disk; nothing written")
        return 2
    development, held_out = load_openings(files)
    if not development:
        print("stopped: no development-window openings before 2025-07-01; nothing written")
        return 2
    sample = take_sample(development)
    kinds = replay_kinds([row["text"] for row in sample])
    payload = summary(development, held_out, sample, kinds, source_label(files[0]))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(__file__).resolve().parents[2] / "evidence" / "transcript-chats" / run_id
    out.mkdir(parents=True)
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"sampled {payload['n_sampled']} of {payload['n_development']} "
        f"development openings; excluded {held_out} held-out; wrote {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
