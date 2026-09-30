"""Orchestrator seam and its deterministic mock.

The endpoint depends only on the `Orchestrator` protocol. Phase 2 swaps the
mock for the real orchestrator without touching contracts or endpoints.

The mock returns *intent*: a message key, or the customer's own words when
they describe a charge. It never invents amounts, dates, or merchants - those
always come from the Gold row - and it never emits prose, so all user-visible
text is translated in the interface.
"""

from dataclasses import dataclass, field
from typing import Protocol

from app.chat.stores import CaseStore

AGENT_WORDS = ("human", "agent", "person", "humano", "agente", "persona", "atendente")
DISPUTE_WORDS = (
    "dispute", "disputa", "charge", "cargo", "cobro", "cobranca", "cobrança",
    "reclamo", "desconozco", "$",
)
RISK_WORDS = ("stolen", "robad", "fraud", "fraude", "urgent", "urgente")
BROKEN_WORDS = ("broken", "falla", "error test")


@dataclass(frozen=True)
class TextDecision:
    message_key: str


@dataclass(frozen=True)
class ClarificationDecision:
    message_key: str
    missing: str


@dataclass(frozen=True)
class OpenCaseDecision:
    """The customer stated these facts; the service resolves the transaction."""

    statement: str
    priority: str
    pre_created_id: str | None = None


@dataclass(frozen=True)
class ChooseTransactionDecision:
    """The customer explicitly picked one of the presented candidates."""

    reference: str
    priority: str


@dataclass(frozen=True)
class EscalateDecision:
    reason_key: str
    priority: str


Decision = (
    TextDecision
    | ClarificationDecision
    | OpenCaseDecision
    | ChooseTransactionDecision
    | EscalateDecision
)


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
            return EscalateDecision(reason_key="reasonAgentButton", priority="Normal")
        if any(word in text for word in AGENT_WORDS):
            asks = self.agent_asks.get(customer_id, 0) + 1
            self.agent_asks[customer_id] = asks
            if asks == 1:
                return TextDecision(message_key="agentSingleOffer")
            return EscalateDecision(reason_key="reasonCustomerAsked", priority="Normal")
        self.agent_asks.pop(customer_id, None)
        if any(word in text for word in BROKEN_WORDS):
            staged = self.cases.create(
                customer_id, "10.00", "MXN", "ACME Store", "2026-06-10", "Open", "Low"
            )
            self.cases.delete(staged.case_id)
            return OpenCaseDecision(
                statement="the charge of 10.00 at ACME Store on 2026-06-10",
                priority="Low",
                pre_created_id=staged.case_id,
            )
        if any(word in text for word in RISK_WORDS):
            return EscalateDecision(reason_key="reasonHighRisk", priority="High")
        if any(word in text for word in DISPUTE_WORDS):
            if len(message) < 25:
                return ClarificationDecision(
                    message_key="clarifyWhichCharge", missing="transaction"
                )
            # The mock echoes the customer's own words back as the statement,
            # so grounding - not keyword routing - decides whether a case opens.
            return OpenCaseDecision(statement=message, priority="High")
        return TextDecision(message_key="greetingHelp")
