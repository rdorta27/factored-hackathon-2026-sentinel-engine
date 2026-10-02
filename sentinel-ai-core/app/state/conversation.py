"""Conversation state per session, behind one port with two adapters.

The state includes the customer's turns (context for the model, REQ-0001), so
it lives exactly as long as the session: deleted on logout and on expiry
(REQ-0027). Keys are hashes of the session token, never the token itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session as DbSession

from app.models.conversation import ConversationRecord
from app.orchestrator.types import (
    Candidate,
    ConversationState,
    Language,
    PendingConfirmation,
    TransactionStatus,
)


@dataclass
class StoredConversation:
    """The orchestrator state plus what the service keeps across turns.

    ``history`` is one structured entry per turn (intent, charge, reply, rule;
    never the customer's words) and ``actions`` every step the system attempted,
    tagged with its turn. Both feed the handoff package and die with the session.
    """

    state: ConversationState
    pending_reason: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    # Set once the history/actions bound has discarded entries (REQ-0001/REQ-0027).
    overflow: bool = False


def token_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def to_json(state: ConversationState) -> str:
    return json.dumps(asdict(state))


def _dump(conversation: StoredConversation) -> str:
    return json.dumps(
        {
            "state": asdict(conversation.state),
            "history": conversation.history,
            "actions": conversation.actions,
            "overflow": conversation.overflow,
        }
    )


def _load(raw: str, pending_reason: str | None) -> StoredConversation:
    data = json.loads(raw)
    if "state" not in data:  # rows written before history existed
        return StoredConversation(from_json(raw), pending_reason)
    return StoredConversation(
        from_json(json.dumps(data["state"])),
        pending_reason,
        list(data.get("history", [])),
        list(data.get("actions", [])),
        bool(data.get("overflow", False)),
    )


def from_json(raw: str) -> ConversationState:
    data = json.loads(raw)
    pending = data.get("pending_confirmation")
    return ConversationState(
        language=Language(data["language"]),
        turns=list(data.get("turns", [])),
        candidates=[
            Candidate(**{**item, "status": TransactionStatus(item["status"])})
            for item in data.get("candidates", [])
        ],
        pending_confirmation=PendingConfirmation(**pending) if pending else None,
        clarification_count=int(data.get("clarification_count", 0)),
        states_not_theirs=bool(data.get("states_not_theirs", False)),
        person_asks=int(data.get("person_asks", 0)),
        rejected_ids=list(data.get("rejected_ids", [])),
        sys_questions=list(data.get("sys_questions", []))[-2:],
    )


class ConversationStore(Protocol):
    def get(self, token: str) -> StoredConversation | None: ...

    def save(self, token: str, conversation: StoredConversation) -> None: ...

    def delete(self, token: str) -> None: ...


class InMemoryConversationStore:
    def __init__(self) -> None:
        self.items: dict[str, StoredConversation] = {}

    def get(self, token: str) -> StoredConversation | None:
        return self.items.get(token_key(token))

    def save(self, token: str, conversation: StoredConversation) -> None:
        self.items[token_key(token)] = conversation

    def delete(self, token: str) -> None:
        self.items.pop(token_key(token), None)


class SqliteConversationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self, token: str) -> StoredConversation | None:
        with DbSession(self._engine) as db:
            row = db.get(ConversationRecord, token_key(token))
            if row is None:
                return None
            return _load(row.state, row.pending_reason)

    def save(self, token: str, conversation: StoredConversation) -> None:
        with DbSession(self._engine) as db, db.begin():
            key = token_key(token)
            row = db.get(ConversationRecord, key)
            if row is None:
                db.add(
                    ConversationRecord(
                        session_id=key,
                        state=_dump(conversation),
                        pending_reason=conversation.pending_reason,
                    )
                )
            else:
                row.state = _dump(conversation)
                row.pending_reason = conversation.pending_reason

    def delete(self, token: str) -> None:
        with DbSession(self._engine) as db, db.begin():
            db.execute(delete(ConversationRecord).where(ConversationRecord.session_id == token_key(token)))

    def count(self) -> int:
        with DbSession(self._engine) as db:
            return len(db.scalars(select(ConversationRecord.session_id)).all())
