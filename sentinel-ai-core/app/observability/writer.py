"""Dual sink for turn records: in-memory list for tests, JSONL file for the runner."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from pathlib import Path

from app.observability.records import StepRecord

logger = logging.getLogger("sentinel.observability")

SALT_ENV = "SENTINEL_SESSION_SALT"
DEFAULT_PATH = Path("var") / "turns.jsonl"


class Recorder:
    """Collects records in memory and appends them as JSON lines to a file."""

    def __init__(self, path: Path | str | None = DEFAULT_PATH, salt: str | None = None) -> None:
        self._path = Path(path) if path is not None else None
        if salt is not None:
            self.salt = salt
            self.ephemeral_salt = False
        else:
            env_salt = os.environ.get(SALT_ENV)
            if env_salt:
                self.salt = env_salt
                self.ephemeral_salt = False
            else:
                self.salt = secrets.token_hex(16)
                self.ephemeral_salt = True
                logger.warning("%s is unset; using an ephemeral salt for session_ref", SALT_ENV)
        self._records: list[StepRecord] = []
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def records(self) -> list[StepRecord]:
        return list(self._records)

    def session_ref(self, session_id: str) -> str:
        digest = hashlib.sha256(f"{self.salt}{session_id}".encode("utf-8")).hexdigest()
        return digest[:16]

    def emit(self, record: StepRecord) -> None:
        self._records.append(record)
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(record.to_json() + "\n")

    def records_for(self, trace_id: str) -> list[StepRecord]:
        return [record for record in self._records if record.trace_id == trace_id]
