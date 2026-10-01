"""Turn-scoped helper that emits step records through a Recorder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.observability.records import StepRecord
from app.observability.writer import Recorder


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TurnObserver:
    """Carries the turn context step() needs to emit records."""

    recorder: Recorder
    trace_id: str
    session_ref: str
    country: str

    def emit(
        self,
        *,
        step: str,
        language: str,
        tool: str | None = None,
        outcome: str = "ok",
        attempt: int = 1,
        policy_rule: str | None = None,
        latency_ms: float = 0.0,
        model: str = "fake",
        route: str = "mock",
        prompt_version: str = "none",
        tokens_in: int = 0,
        tokens_out: int = 0,
        cost_usd: float = 0.0,
        event: str | None = None,
        handoff: dict | None = None,
        policy_version: str | None = None,
        policy_synthetic: bool | None = None,
    ) -> None:
        self.recorder.emit(
            StepRecord(
                ts=utc_now(),
                trace_id=self.trace_id,
                session_ref=self.session_ref,
                step=step,
                tool=tool,
                outcome=outcome,
                attempt=attempt,
                policy_rule=policy_rule,
                latency_ms=latency_ms,
                model=model,
                route=route,
                prompt_version=prompt_version,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost_usd,
                language=language,
                country=self.country,
                event=event,
                handoff=handoff,
                policy_version=policy_version,
                policy_synthetic=policy_synthetic,
            )
        )
