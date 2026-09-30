"""Offline replay of recorded model responses."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.ai.transport import LLMResponse, ModelUnavailable


def normalize_input(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def input_hash(message: str, turns: list[str] | None = None) -> str:
    joined = normalize_input(message) + "\n" + "\n".join(
        normalize_input(turn) for turn in (turns or [])[-4:]
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def fixture_filename(prompt_version: str, digest: str) -> str:
    safe_version = re.sub(r"[^A-Za-z0-9_.-]", "_", prompt_version)
    return f"{safe_version}-{digest}.json"


class FixtureTransport:
    """Serve committed JSON fixtures without opening any connection."""

    def __init__(self, fixtures_dir: Path | str, prompt_version: str = "v1") -> None:
        self._dir = Path(fixtures_dir)
        self._prompt_version = prompt_version

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        user_text = ""
        for entry in reversed(messages):
            if entry.get("role") == "user":
                user_text = str(entry.get("content", ""))
                break
        digest = input_hash(user_text, [user_text])
        path = self._dir / fixture_filename(self._prompt_version, digest)
        if not path.is_file():
            raise ModelUnavailable(f"no fixture for input hash {digest}")
        body = json.loads(path.read_text(encoding="utf-8"))
        if body.get("prompt_version") != self._prompt_version:
            raise ModelUnavailable("fixture prompt version mismatch")
        return LLMResponse(
            content=json.dumps(body.get("response", {})),
            tokens_in=int(body.get("tokens_in", 0) or 0),
            tokens_out=int(body.get("tokens_out", 0) or 0),
            cost_usd=float(body.get("cost_usd", 0.0) or 0.0),
        )
