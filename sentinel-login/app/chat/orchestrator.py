"""Orchestrator seam and its deterministic mock.

The endpoint depends only on the `Orchestrator` protocol. Phase 2 swaps the
mock for the real orchestrator without touching contracts or endpoints.
"""

import re
from dataclasses import dataclass, field
from typing import Protocol

from app.chat.stores import CaseStore

AGENT_WORDS = ("human", "agent", "person", "humano", "agente", "persona", "atendente")
DISPUTE_WORDS = ("dispute", "charge", "cargo", "cobro", "desconozco", "reclamo", "$")
RISK_WORDS = ("stolen", "robad", "fraud", "fraude", "urgent", "urgente")
BROKEN_WORDS = ("broken", "falla", "error test")


@dataclass(frozen=True)
class TextDecision:
    text: str


@dataclass(frozen=True)
class ClarificationDecision:
    text: str
    missing: str


@dataclass(frozen=True)
class OpenCaseDecision:
    reference: str
    priority: str
    pre_created_id: str | None = None


@dataclass(frozen=True)
class EscalateDecision:
    reason: str
    priority: str


Decision = TextDecision | ClarificationDecision | OpenCaseDecision | EscalateDecision


class Orchestrator(Protocol):
    """Decides the next step for a customer message. Never touches sessions."""

    def decide(self, message: str, customer_id: str) -> Decision:
        ...


@dataclass
class MockOrchestrator:
    """Deterministic keyword router over the four demo scenarios.

    Mock-sourced by construction (see the `source` field on replies).
    Holds the case store only for the broken-write scenario.
    """

    cases: CaseStore
    agent_asks: dict[str, int] = field(default_factory=dict)

    def decide(self, message: str, customer_id: str) -> Decision:
        text = message.lower()
        if "escalate now" in text:
            self.agent_asks.pop(customer_id, None)
            return EscalateDecision(
                reason="Customer used the agent button", priority="Normal"
            )
        if any(word in text for word in AGENT_WORDS):
            asks = self.agent_asks.get(customer_id, 0) + 1
            self.agent_asks[customer_id] = asks
            if asks == 1:
                return TextDecision(
                    "I can keep helping here, or connect you with an agent. "
                    "Mention an agent again and I will escalate right away."
                )
            return EscalateDecision(
                reason="Customer asked for a human", priority="Normal"
            )
        if not any(word in text for word in AGENT_WORDS):
            self.agent_asks.pop(customer_id, None)
        if any(word in text for word in BROKEN_WORDS):
            staged = self.cases.create(
                customer_id, "10.00", "MXN", "ACME Store", "2026-06-10", "Open", "Low"
            )
            self.cases.delete(staged.case_id)
            return OpenCaseDecision(
                reference="TXN-1001",
                priority="Low",
                pre_created_id=staged.case_id,
            )
        if any(word in text for word in RISK_WORDS):
            return EscalateDecision(
                reason="High-risk indicators in the message", priority="High"
            )
        if any(word in text for word in DISPUTE_WORDS):
            if len(message) < 25 and not re.search(r"\d", message):
                return ClarificationDecision(
                    text="Which charge looks wrong? Tell me the amount or the store.",
                    missing="transaction",
                )
            if "stale" in text or "old" in text or "january" in text:
                return OpenCaseDecision(reference="TXN-1002", priority="High")
            if "refund" in text or "reembolso" in text:
                return OpenCaseDecision(reference="TXN-1003", priority="High")
            return OpenCaseDecision(reference="TXN-1001", priority="High")
        return TextDecision(
            "I can help with transaction disputes. Tell me which charge looks wrong."
        )
