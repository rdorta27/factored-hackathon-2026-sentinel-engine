"""Drive a running app through one fault and report the safe-reply share.

The app under test runs with the matching ``SENTINEL_FAULT_*`` set; this
script only drives it over HTTP with ``sentinel_client.py`` and prints one
JSON summary to standard output. It never writes under ``evidence/``: the
frozen run after the code freeze does that.

Fault label to server setting:

- ``model-timeout``: ``SENTINEL_FAULT_MODEL=timeout``
- ``model-5xx``: ``SENTINEL_FAULT_MODEL=error_5xx``
- ``model-json``: ``SENTINEL_FAULT_MODEL=invalid_json``
- ``gold-slow``: ``SENTINEL_FAULT_GOLD=slow``
- ``gold-error``: ``SENTINEL_FAULT_GOLD=error``
- ``store-error``: ``SENTINEL_FAULT_STORE=error``
- ``none``: no fault, the healthy baseline of the same script.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinel_client import SentinelClient

SAFE_KINDS = frozenset(
    {
        "text",
        "clarification",
        "confirm_box",
        "explanation",
        "case_confirmation",
        "handoff",
        "error",
    }
)
LEAK_MARKERS = ("Traceback", "File \"", "fault injection")

SCRIPT = (
    {"message": "hola"},
    {"message": "no reconozco un cargo de ACME Store"},
    {"message": "quiero un préstamo"},
    {"message": "quiero hablar con una persona"},
)


def _is_safe(status: int, text: str, body: dict) -> bool:
    if status != 200 or not isinstance(body, dict):
        return False
    if body.get("kind") not in SAFE_KINDS:
        return False
    return not any(marker in text for marker in LEAK_MARKERS)


def _drive(client: SentinelClient, payload: dict, timeout: float) -> tuple[bool, float, str]:
    started = time.perf_counter()
    try:
        response = client.post("/api/v1/chat", json=payload, timeout=timeout)
        latency_ms = (time.perf_counter() - started) * 1000.0
        try:
            body = response.json()
        except ValueError:
            return False, latency_ms, "unparseable"
        kind = body.get("kind") if isinstance(body, dict) else None
        if kind == "confirm_box":
            reference = ((body.get("candidate") or {}).get("reference"))
            if reference:
                follow = client.post(
                    "/api/v1/chat", json={"selected_reference": reference}, timeout=timeout
                )
                return _is_safe(follow.status_code, follow.text, _json_or_none(follow)), latency_ms, "confirm_box"
        return _is_safe(response.status_code, response.text, body), latency_ms, str(kind)
    except Exception as exc:  # noqa: BLE001 - a transport failure is an unsafe turn
        return False, (time.perf_counter() - started) * 1000.0, f"client_error:{type(exc).__name__}"


def _json_or_none(response):  # type: ignore[no-untyped-def]
    try:
        return response.json()
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Drive one fault against a running app.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--fault", default="none")
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--login", default="CUST-0001")
    parser.add_argument("--password", default="Testpass-001")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    kinds: dict[str, int] = {}
    latencies: list[float] = []
    safe = 0
    total = 0
    with SentinelClient(args.base_url, timeout=args.timeout) as client:
        client.login(args.login, args.password)
        for _ in range(args.rounds):
            for payload in SCRIPT:
                ok, latency_ms, kind = _drive(client, dict(payload), args.timeout)
                total += 1
                safe += 1 if ok else 0
                latencies.append(latency_ms)
                kinds[kind] = kinds.get(kind, 0) + 1
    summary = {
        "fault": args.fault,
        "turns": total,
        "safe_turns": safe,
        "safe_share": safe / total if total else 0.0,
        "latency_ms": {
            "p50": statistics.median(latencies) if latencies else 0.0,
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0),
            "max": max(latencies) if latencies else 0.0,
        },
        "kinds": kinds,
    }
    print(json.dumps(summary, indent=2))
    return 0 if safe == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
