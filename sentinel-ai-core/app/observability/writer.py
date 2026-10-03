"""Turn-record sinks: memory, a JSONL file, and optional standard output."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sys
from pathlib import Path

from app.observability.records import StepRecord

logger = logging.getLogger("sentinel.observability")
_stdout = logging.getLogger("sentinel.turns")

SALT_ENV = "SENTINEL_SESSION_SALT"
VAR_DIR_ENV = "SENTINEL_VAR_DIR"
STDOUT_ENV = "SENTINEL_LOG_STDOUT"
DEFAULT_PATH = Path("var") / "turns.jsonl"


def require_writable(directory: Path) -> None:
    """Create ``directory`` if needed and fail if this process cannot write a file there."""
    if not directory.exists():
        directory.mkdir(parents=True, mode=0o700)
    if not os.access(directory, os.W_OK | os.X_OK):
        raise OSError(f"state path is not writable: {directory}")
    probe = directory / f".write-probe-{os.getpid()}"
    try:
        fd = os.open(probe, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        os.unlink(probe)
    except OSError as exc:
        raise OSError(f"state path is not writable: {directory}") from exc


def _emit_stdout(line: str) -> None:
    """Print one record line, with no prefix, on the current standard output."""
    if not _stdout.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        _stdout.addHandler(handler)
        _stdout.setLevel(logging.INFO)
        _stdout.propagate = False
    else:
        _stdout.handlers[0].setStream(sys.stdout)
    _stdout.info(line)


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
            require_writable(self._path.parent)
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
        line = record.to_json()
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        if os.environ.get(STDOUT_ENV) == "1":
            _emit_stdout(line)

    def records_for(self, trace_id: str) -> list[StepRecord]:
        return [record for record in self._records if record.trace_id == trace_id]
