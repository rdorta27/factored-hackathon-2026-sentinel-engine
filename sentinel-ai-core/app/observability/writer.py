"""Dual sink for turn records: in-memory list for tests, JSONL file for the runner."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from pathlib import Path

from app.observability.records import StepRecord

logger = logging.getLogger("sentinel.observability")

SALT_ENV = "SENTINEL_SESSION_SALT"
VAR_DIR_ENV = "SENTINEL_VAR_DIR"
DEFAULT_PATH = Path("var") / "turns.jsonl"


def var_dir() -> Path:
    """Canonical runtime directory, independent of the process CWD.

    Resolves to ``SENTINEL_VAR_DIR`` when set (tests), otherwise to the
    ``var/`` folder next to the installed ``app`` package, so launching from
    the repo root can no longer scatter a second ``var/`` tree.
    """
    override = os.environ.get(VAR_DIR_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "var"


def _touch_private(path: Path) -> None:
    """Create the log owner-only (0600); the turn log is read by the operator only."""
    os.close(os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600))


class Recorder:
    """Collects records in memory and appends them as JSON lines to a file."""

    def __init__(self, path: Path | str | None = DEFAULT_PATH, salt: str | None = None) -> None:
        if path is DEFAULT_PATH or (isinstance(path, Path) and path == DEFAULT_PATH):
            path = var_dir() / "turns.jsonl"
        self._path = Path(path) if path is not None else None
        self.salt, self.ephemeral_salt = self._resolve_salt(salt)
        self._records: list[StepRecord] = []
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            _touch_private(self._path)

    @staticmethod
    def _resolve_salt(explicit: str | None) -> tuple[str, bool]:
        """Salt order: explicit argument, environment, persisted dev file,
        generated. The dev file lives beside the log output (gitignored), so
        restarts correlate without ever committing a secret."""
        if explicit is not None:
            return explicit, False
        env_salt = os.environ.get(SALT_ENV)
        if env_salt:
            return env_salt, False
        salt_file = var_dir() / ".session_salt"
        if salt_file.is_file():
            return salt_file.read_text(encoding="utf-8").strip(), False
        generated = secrets.token_hex(16)
        try:
            salt_file.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(salt_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(generated)
        except OSError:
            logger.warning("%s is unset; using an ephemeral salt for session_ref", SALT_ENV)
            return generated, True
        logger.warning(
            "%s is unset; generated a dev salt at %s (gitignored, demo only)",
            SALT_ENV,
            salt_file,
        )
        return generated, False

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

    def persisted_for(self, trace_id: str) -> list[StepRecord]:
        """Read one trace back from the JSONL log.

        Used when the turn is no longer in memory (a restart): the advisor
        trace route falls back to the file. Unknown or corrupt lines are
        skipped rather than failing the request.
        """
        if self._path is None or not self._path.is_file():
            return []
        found: list[StepRecord] = []
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("trace_id") != trace_id:
                    continue
                try:
                    found.append(StepRecord(**data))
                except (TypeError, ValueError):
                    continue
        return found
