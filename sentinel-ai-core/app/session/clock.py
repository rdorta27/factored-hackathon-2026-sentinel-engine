import os
from datetime import date

ENV_VAR = "SENTINEL_REFERENCE_DATE"
DEFAULT_REFERENCE_DATE = "2026-06-17"


def reference_date() -> date:
    raw = os.environ.get(ENV_VAR, DEFAULT_REFERENCE_DATE)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.fromisoformat(DEFAULT_REFERENCE_DATE)
