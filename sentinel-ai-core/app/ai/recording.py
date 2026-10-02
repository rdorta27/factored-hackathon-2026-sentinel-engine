"""Recordings keyed by model, prompt version, input and repetition.

Unlike the ``v1-<hash>.json`` fixtures, which carry no model, a recording
here belongs to one model and one repetition, so two candidates or two
repetitions of the same input never share a file. Files are named
``rec-<key>.json`` and store the four key parts in clear text next to the
raw reply, so an invalid reply replays as invalid.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from app.ai.fixtures import _underlying, input_hash
from app.ai.transport import LLMResponse, ModelUnavailable

PREFIX = "rec-"


def recording_key(model: str, prompt_version: str, digest: str, repetition: int) -> str:
    joined = "\n".join((model, prompt_version, digest, str(int(repetition))))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def recording_filename(key: str) -> str:
    return f"{PREFIX}{re.sub(r'[^0-9a-f]', '', key)}.json"


def user_digest(messages: list[dict[str, str]]) -> str:
    user_text = ""
    for entry in reversed(messages):
        if entry.get("role") == "user":
            user_text = str(entry.get("content", ""))
            break
    message, turns = _underlying(user_text)
    return input_hash(message, turns)


def write_recording(
    path: Path,
    *,
    model: str,
    prompt_version: str,
    digest: str,
    repetition: int,
    messages: list[dict[str, str]],
    response: LLMResponse,
) -> None:
    user_text = next(
        (str(e.get("content", "")) for e in reversed(messages) if e.get("role") == "user"), ""
    )
    message, turns = _underlying(user_text)
    body = {
        "model": model,
        "prompt_version": prompt_version,
        "input_hash": digest,
        "repetition": int(repetition),
        "input": {"message": message, "turns": turns},
        "content": response.content,
        "tokens_in": response.tokens_in,
        "tokens_out": response.tokens_out,
        "cost_usd": response.cost_usd,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class RecordedTransport:
    """Replay recordings for one prompt version without opening a connection.

    ``repetition`` selects which recorded repetition to serve; the bench sets
    it before each pass.
    """

    def __init__(self, recordings_dir: Path | str, prompt_version: str, repetition: int = 0) -> None:
        self._dir = Path(recordings_dir)
        self.prompt_version = prompt_version
        self.repetition = repetition

    def path_for(self, model: str, messages: list[dict[str, str]]) -> tuple[Path, str]:
        digest = user_digest(messages)
        key = recording_key(model, self.prompt_version, digest, self.repetition)
        return self._dir / recording_filename(key), digest

    def read(self, path: Path, model: str) -> LLMResponse:
        body = json.loads(path.read_text(encoding="utf-8"))
        if body.get("model") != model or body.get("prompt_version") != self.prompt_version:
            raise ModelUnavailable(f"recording {path.name} does not match its key")
        return LLMResponse(
            content=str(body.get("content", "")),
            tokens_in=int(body.get("tokens_in", 0) or 0),
            tokens_out=int(body.get("tokens_out", 0) or 0),
            cost_usd=float(body.get("cost_usd", 0.0) or 0.0),
        )

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        path, digest = self.path_for(model, messages)
        if not path.is_file():
            raise ModelUnavailable(f"no recording for {model} input {digest} repetition {self.repetition}")
        return self.read(path, model)


__all__ = [
    "PREFIX",
    "RecordedTransport",
    "recording_filename",
    "recording_key",
    "user_digest",
    "write_recording",
]
