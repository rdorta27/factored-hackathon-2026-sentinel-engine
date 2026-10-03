"""Structured turn records: the internal receipt of every turn (see
docs/architecture/specification.md, Observability section)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re

STEPS = frozenset({"understand", "decide", "act", "verify", "escalate", "session", "turn"})
OUTCOMES = frozenset({"ok", "rejected", "failed", "timeout"})
LANGUAGES = frozenset({"es-419", "pt-BR"})
COUNTRIES = frozenset({"MX", "CO", "AR"})
HEX16 = re.compile(r"^[0-9a-f]{16}$")
_CUSTOMER_ID = re.compile(r"CUST-\d+|CLI-[A-Z0-9]{8,}")
_IPV4 = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def _reject_pii(field: str, value: str) -> None:
    if _CUSTOMER_ID.search(value) or _IPV4.search(value):
        raise ValueError(f"personal data is never logged: {field}")


@dataclass(frozen=True)
class StepRecord:
    """One JSON line per loop step, session event, or turn closing record."""

    ts: str
    trace_id: str
    session_ref: str
    step: str
    tool: str | None
    outcome: str
    attempt: int
    policy_rule: str | None
    latency_ms: float
    model: str
    route: str
    prompt_version: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    language: str
    country: str
    event: str | None = None
    handoff: dict | None = None
    # What the model detected from the text, kept beside the answered `language`
    # so the record reports both and contradicts neither.
    detected_language: str | None = None
    # Country policy file version and whether it is the team's synthetic policy.
    policy_version: str | None = None
    policy_synthetic: bool | None = None

    def __post_init__(self) -> None:
        if not HEX16.match(self.trace_id):
            raise ValueError("trace_id must be 16 hex chars")
        if not HEX16.match(self.session_ref):
            raise ValueError("session_ref must be a 16-char salted hash, never an identifier")
        if self.step not in STEPS:
            raise ValueError(f"step must be one of {sorted(STEPS)}")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {sorted(OUTCOMES)}")
        if self.attempt < 1:
            raise ValueError("attempt must be 1 or higher")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be 0 or higher")
        if self.tokens_in < 0 or self.tokens_out < 0:
            raise ValueError("token counts must be 0 or higher")
        if self.cost_usd < 0:
            raise ValueError("cost_usd must be 0 or higher")
        if not self.model or not self.route or not self.prompt_version:
            raise ValueError("model, route and prompt_version are never empty")
        if self.language not in LANGUAGES:
            raise ValueError(f"language must be one of {sorted(LANGUAGES)}")
        if self.country not in COUNTRIES:
            raise ValueError(f"country must be one of {sorted(COUNTRIES)}")
        for field in ("tool", "policy_rule", "model", "route", "prompt_version", "event"):
            value = getattr(self, field)
            if value is not None:
                _reject_pii(field, value)
        if self.handoff is not None:
            _reject_pii("handoff", json.dumps(self.handoff))

    def to_json(self) -> str:
        return json.dumps(asdict(self))
