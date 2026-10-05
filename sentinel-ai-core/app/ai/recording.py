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
from time import perf_counter

from app.ai.fixtures import _underlying, input_hash
from app.ai.transport import (
    LLMResponse,
    ModelTransport,
    ModelUnavailable,
    logprobs_from_json,
    logprobs_to_json,
)

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
    latency_ms: float = 0.0,
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
        "latency_ms": round(float(latency_ms), 1),
    }
    # Keep the label token's alternatives so a calibration run can derive the
    # confidence offline, from the recording, without a second live call.
    logprobs = logprobs_to_json(response.logprobs)
    if logprobs is not None:
        body["logprobs"] = logprobs
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
        # Latency of the live call behind the last reply served, so a replay
        # reports model latency instead of the time to read a file.
        self.last_latency_ms = 0.0

    def path_for(self, model: str, messages: list[dict[str, str]]) -> tuple[Path, str]:
        digest = user_digest(messages)
        key = recording_key(model, self.prompt_version, digest, self.repetition)
        return self._dir / recording_filename(key), digest

    def read(self, path: Path, model: str) -> LLMResponse:
        body = json.loads(path.read_text(encoding="utf-8"))
        if body.get("model") != model or body.get("prompt_version") != self.prompt_version:
            raise ModelUnavailable(f"recording {path.name} does not match its key")
        self.last_latency_ms = float(body.get("latency_ms", 0.0) or 0.0)
        return LLMResponse(
            content=str(body.get("content", "")),
            tokens_in=int(body.get("tokens_in", 0) or 0),
            tokens_out=int(body.get("tokens_out", 0) or 0),
            cost_usd=float(body.get("cost_usd", 0.0) or 0.0),
            logprobs=logprobs_from_json(body.get("logprobs")),
        )

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.last_latency_ms = 0.0
        path, digest = self.path_for(model, messages)
        if not path.is_file():
            raise ModelUnavailable(f"no recording for {model} input {digest} repetition {self.repetition}")
        return self.read(path, model)


class SecretInRecording(RuntimeError):
    """A recording would carry the API key or a credential header."""


_CREDENTIAL_MARKS = ("authorization", "bearer ")


def assert_no_secret(text: str, api_key: str) -> None:
    lowered = text.lower()
    if api_key and api_key in text:
        raise SecretInRecording("recording would contain the API key; nothing was written")
    for mark in _CREDENTIAL_MARKS:
        if mark in lowered:
            raise SecretInRecording(f"recording would contain {mark.strip()!r}; nothing was written")


class RecordingTransport(RecordedTransport):
    """Serve a recording on a hit; call the live transport on a miss only when recording.

    Outside recording mode a miss raises, so an evaluation never makes an
    unplanned live call. The API key is passed in only to check that it never
    reaches a written file.
    """

    def __init__(
        self,
        recordings_dir: Path | str,
        prompt_version: str,
        live: ModelTransport | None = None,
        *,
        record: bool = False,
        api_key: str = "",
        repetition: int = 0,
        force_live: bool = False,
    ) -> None:
        super().__init__(recordings_dir, prompt_version, repetition)
        self._live = live
        self._record = record
        self._api_key = api_key
        # Live timing mode: ignore an existing recording and call the model, so
        # every call is a live sample. The write keeps the run reproducible.
        self._force_live = force_live
        self.live_calls = 0
        self.spent_usd = 0.0

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        self.last_latency_ms = 0.0
        path, digest = self.path_for(model, messages)
        if path.is_file() and not self._force_live:
            return self.read(path, model)
        if not self._record or self._live is None:
            raise ModelUnavailable(
                f"no recording for {model} input {digest} repetition {self.repetition} (not recording)"
            )
        started = perf_counter()
        response = self._live.complete(model=model, messages=messages, temperature=temperature)
        self.last_latency_ms = (perf_counter() - started) * 1000
        self.live_calls += 1
        self.spent_usd += response.cost_usd
        recorded_blob = response.content + json.dumps(messages, ensure_ascii=False)
        if response.logprobs is not None:
            recorded_blob += json.dumps(logprobs_to_json(response.logprobs), ensure_ascii=False)
        assert_no_secret(recorded_blob, self._api_key)
        write_recording(
            path,
            model=model,
            prompt_version=self.prompt_version,
            digest=digest,
            repetition=self.repetition,
            messages=messages,
            response=response,
            latency_ms=self.last_latency_ms,
        )
        return response


__all__ = [
    "PREFIX",
    "RecordingTransport",
    "SecretInRecording",
    "assert_no_secret",
    "RecordedTransport",
    "recording_filename",
    "recording_key",
    "user_digest",
    "write_recording",
]
