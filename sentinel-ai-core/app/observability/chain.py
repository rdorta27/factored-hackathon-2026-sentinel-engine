"""Hash-chained audit records (REQ-0025, REQ-0029).

Each record holds the hash of the one before, so a changed or removed
record breaks the chain at a named position. The recorder chains on emit;
``verify_chain`` checks memory or file-backed records the same way.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

from app.observability.records import StepRecord

GENESIS = ""


def canonical(record: StepRecord) -> str:
    """Stable bytes of the record content, without the chain fields."""
    data = asdict(record)
    data.pop("prev_hash", None)
    data.pop("record_hash", None)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def record_hash(record: StepRecord, prev_hash: str) -> str:
    digest = hashlib.sha256(f"{prev_hash}\n{canonical(record)}".encode("utf-8")).hexdigest()
    return digest


def chain_record(record: StepRecord, prev_hash: str) -> StepRecord:
    return replace(record, prev_hash=prev_hash, record_hash=record_hash(record, prev_hash))


def verify_chain(records: list[StepRecord]) -> int | None:
    """Index of the first record that breaks the chain, or None when whole."""
    expected = GENESIS
    for index, record in enumerate(records):
        if record.prev_hash != expected:
            return index
        if record.record_hash != record_hash(record, record.prev_hash):
            return index
        expected = record.record_hash
    return None
