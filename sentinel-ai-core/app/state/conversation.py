"""Conversation state per session, behind one port with two adapters.

The state includes the customer's turns (context for the model, REQ-0001), so
it lives exactly as long as the session: deleted on logout and on expiry
(REQ-0027). Keys are hashes of the session token, never the token itself.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

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
    """The orchestrator state plus what the disputes API keeps between its two steps."""

    state: ConversationState
    pending_reason: str | None = None


def token_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def to_json(state: ConversationState) -> str:
    return json.dumps(asdict(state))


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
        person_asks=int(data.get("person_asks", 0)),
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
            return StoredConversation(from_json(row.state), row.pending_reason)

    def save(self, token: str, conversation: StoredConversation) -> None:
        with DbSession(self._engine) as db, db.begin():
            key = token_key(token)
            row = db.get(ConversationRecord, key)
            if row is None:
                db.add(
                    ConversationRecord(
                        session_id=key,
                        state=to_json(conversation.state),
                        pending_reason=conversation.pending_reason,
                    )
                )
            else:
                row.state = to_json(conversation.state)
                row.pending_reason = conversation.pending_reason

    def delete(self, token: str) -> None:
        with DbSession(self._engine) as db, db.begin():
            db.execute(delete(ConversationRecord).where(ConversationRecord.session_id == token_key(token)))

    def count(self) -> int:
        with DbSession(self._engine) as db:
            return len(db.scalars(select(ConversationRecord.session_id)).all())
