import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("sentinel.audit")


class AuditLogger:
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
