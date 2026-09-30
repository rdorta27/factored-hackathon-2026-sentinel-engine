"""Session auth events as observability records.

Auth events ride the shared Recorder as `step: session` records. The
customer is never logged: sessions travel as a salted hash and the client
IP is not recorded at all.
"""

from __future__ import annotations

from app.observability.observer import utc_now
from app.observability.records import StepRecord
from app.observability.writer import Recorder

ANONYMOUS_ID = "anonymous"


class AuditLogger:
    def __init__(self, recorder: Recorder) -> None:
        self._recorder = recorder

    @property
    def records(self) -> list[StepRecord]:
        return [record for record in self._recorder.records if record.step == "session"]

    def emit(
        self,
        event: str,
        trace_id: str,
        session_id: str | None = None,
        language: str = "es-419",
        country: str = "MX",
    ) -> None:
        """Record an auth event. Language and country default to the login
        defaults when the session is not known yet (failed or denied auth)."""
        ref_source = session_id if session_id is not None else ANONYMOUS_ID
        self._recorder.emit(
            StepRecord(
                ts=utc_now(),
                trace_id=trace_id,
                session_ref=self._recorder.session_ref(ref_source),
                step="session",
                tool=None,
                outcome="ok",
                attempt=1,
                policy_rule=None,
                latency_ms=0.0,
                model="fake",
                route="mock",
                prompt_version="none",
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
                language=language,
                country=country,
                event=event,
            )
        )
