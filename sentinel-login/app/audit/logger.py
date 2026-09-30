"""JSON-lines audit log. Never records passwords or full session tokens."""

import hashlib
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("sentinel.audit")


def token_fingerprint(token: str) -> str:
    """Short non-reversible session identifier safe for logs."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


class AuditLogger:
    """Emits one JSON object per line per authentication event."""

    def __init__(self) -> None:
        self.records: list[dict] = []

    def emit(
        self,
        event: str,
        customer_id: str | None,
        trace_id: str,
        ip: str,
    ) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "customer_id": customer_id,
            "trace_id": trace_id,
            "ip": ip,
        }
        self.records.append(record)
        logger.info(json.dumps(record))
