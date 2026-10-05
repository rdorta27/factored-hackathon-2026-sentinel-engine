"""Replay the ten points of the manual test of Felix over HTTP.

Felix tested the demo as a customer on 2026-10-04. This script repeats the ten
points against a running service and writes a pass/fail table to the screen and
to `team/chat-manual-tests.md`. Each point uses a new session. A local run also
uses a clean SQLite file for each point, so one point cannot change the state
that the next point reads.

Points 4 and 8 depend on the model: they stay out of scope for this change
(router-v3). They are reported as "out of scope (router-v3)", not as a failure.

Usage::

    python3 scripts/felix_replay.py
    python3 scripts/felix_replay.py --base-url https://example.test --no-spawn

The default base URL is http://127.0.0.1:8002. On a loopback base URL the
script starts one local uvicorn process per point, on the port of the base URL,
with a temporary SQLite file. With --no-spawn, or on a remote base URL, it uses
the running service and starts nothing.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinel_client import SentinelClient  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "sentinel-ai-core"
REPORT = REPO_ROOT / "team" / "chat-manual-tests.md"
DEFAULT_BASE_URL = "http://127.0.0.1:8002"
REFERENCE_DATE = "2026-06-17"
START = "<!-- felix-replay:start -->"
END = "<!-- felix-replay:end -->"

OUT_OF_SCOPE_ROUTER = "out of scope (router-v3)"


@dataclass(frozen=True)
class Point:
    number: str
    name: str
    check: Callable[[SentinelClient], str] | None
    out_of_scope: str | None = None


@dataclass(frozen=True)
class Result:
    number: str
    name: str
    status: str
    detail: str


# --- the ten points ---------------------------------------------------------


def check_handoff(client: SentinelClient) -> str:
    client.chat(message="quiero una persona")
    filed = client.chat(message="quiero una persona").json()
    assert filed["kind"] == "handoff", f"no handoff, kind {filed.get('kind')}"
    new = client.chat(message="no reconozco el cargo de Cafe Central").json()
    assert new["kind"] == "confirm_box", f"a new charge did not continue: {new.get('kind')}"

    with SentinelClient(client.base_url) as second:
        second.login()
        second.chat(message="quiero una persona")
        second_filed = second.chat(message="quiero una persona").json()
        for _ in range(2):
            second.chat(message="HOLA")
        later = second.chat(message="HOLA").json()
    assert later["kind"] == "handoff", f"the later turn is {later.get('kind')}"
    assert later["reference"] == second_filed["reference"], "the reference changed"
    assert later["reason_key"] == second_filed["reason_key"], "the reason changed"
    return "a new charge continues; the filed reference and reason stay fixed"


def check_dispute_status(client: SentinelClient) -> str:
    client.chat(selected_reference="TXN-1006")
    client.chat(selected_reference="TXN-1006")
    before = client.cases().json()
    reply = client.chat(message="ya abrí una disputa, ¿en qué va?").json()
    assert reply["kind"] == "explanation", f"kind {reply.get('kind')}"
    case_id = before[0]["case_id"] if before else None
    assert case_id and case_id in json.dumps(reply), "the case reference is missing"
    after = client.cases().json()
    assert len(after) == len(before), "a new case was opened"
    return f"answered from the case store ({case_id}); no new case"


def check_correction(client: SentinelClient) -> str:
    client.chat(selected_reference="TXN-1001")
    reply = client.chat(message="no, perdón, el de 320").json()
    assert reply["kind"] == "confirm_box", f"kind {reply.get('kind')}"
    reference = reply["candidate"]["reference"]
    assert reference == "TXN-1006", f"the box shows {reference}"
    return "the box moved from TXN-1001 to TXN-1006"


def check_already_disputed(client: SentinelClient) -> str:
    client.chat(selected_reference="TXN-1006")
    client.chat(selected_reference="TXN-1006")
    before = len(client.cases().json())
    reply = client.chat(selected_reference="TXN-1006").json()
    assert reply["kind"] == "text" and reply["message_key"] == "already.disputed", (
        f"{reply.get('kind')}/{reply.get('message_key')}"
    )
    assert len(client.cases().json()) == before, "a second case was opened"
    return "no box and no second case"


def check_january_why(client: SentinelClient) -> str:
    first = client.chat(message="Hay un cobro de 2500 MXN en ACME Store").json()
    assert first["kind"] == "text" and first["message_key"] == "window.expired", (
        f"{first.get('kind')}/{first.get('message_key')}"
    )
    reply = client.chat(message="¿por qué no puedo el de enero?").json()
    assert reply["kind"] == "explanation", f"kind {reply.get('kind')}"
    assert reply.get("rule_id") == "window.expired", f"rule {reply.get('rule_id')}"
    return "the why follow-up names the window rule"


def check_length(client: SentinelClient) -> str:
    accepted = client.chat(message="a" * 2000)
    assert accepted.status_code == 200, f"2000 characters -> {accepted.status_code}"
    rejected = client.chat(message="a" * 2001)
    assert rejected.status_code == 422, f"2001 characters -> {rejected.status_code}"
    return "2000 accepted, 2001 rejected"


def check_searched_date(client: SentinelClient) -> str:
    yesterday = (date.fromisoformat(client.reference_date()) - timedelta(days=1)).isoformat()
    reply = client.chat(message="algo raro ayer").json()
    assert reply["kind"] == "clarification", f"kind {reply.get('kind')}"
    found = reply.get("values", {}).get("searched_date")
    assert found == yesterday, f"searched_date {found}, wanted {yesterday}"
    return f"the clarification names {yesterday}"


def check_responsive(client: SentinelClient) -> str:
    page = client.get("/ui/")
    assert page.status_code == 200, f"/ui/ -> {page.status_code}"
    assert 'name="viewport"' in page.text, "no viewport meta tag"
    css = client.get("/ui/styles.css")
    assert css.status_code == 200, f"styles.css -> {css.status_code}"
    assert "@media" in css.text, "no responsive media query"
    return "the viewport meta tag and a responsive media query are served"


POINTS = (
    Point("1", "After a handoff, the same ticket and a changing reason", check_handoff),
    Point("2", "A dispute-status question opens another case", check_dispute_status),
    Point("3", "A correction with the box open is ignored", check_correction),
    Point("4", "A loan request enters the dispute flow", None, OUT_OF_SCOPE_ROUTER),
    Point("5", "A box opens for a charge with an open dispute", check_already_disputed),
    Point("6", "Why the January charge cannot be disputed", check_january_why),
    Point("7", "No length limit on the message", check_length),
    Point("8", "An amount in words does not find the charge", None, OUT_OF_SCOPE_ROUTER),
    Point("9", "A date with no match gives no clear answer", check_searched_date),
    Point("10", "The page is not responsive", check_responsive),
)


# --- local server -----------------------------------------------------------


def wait_for_health(base_url: str, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/api/v1/health", timeout=2.0).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"the service at {base_url} did not become healthy")


@contextlib.contextmanager
def local_server(port: int):
    with tempfile.TemporaryDirectory(prefix="felix-replay-") as folder:
        env = os.environ.copy()
        env.update(
            {
                "SENTINEL_STATE_BACKEND": "sqlite",
                "SENTINEL_DB_PATH": str(Path(folder) / "state.db"),
                "SENTINEL_GOLD_SOURCE": "mock",
                "SENTINEL_SECURE_COOKIES": "false",
                "SENTINEL_REFERENCE_DATE": REFERENCE_DATE,
                "SENTINEL_SESSION_SALT": secrets.token_hex(16),
            }
        )
        process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn", "app.main:app",
                "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning",
            ],
            cwd=CORE_DIR,
            env=env,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            wait_for_health(base_url)
            yield base_url
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# --- runner -----------------------------------------------------------------


def run_point(point: Point, base_url: str, manage_server: bool, port: int) -> Result:
    if point.check is None:
        return Result(point.number, point.name, point.out_of_scope or "", "depends on the model")
    try:
        if manage_server:
            with local_server(port) as url:
                with SentinelClient(url) as client:
                    client.login()
                    detail = point.check(client)
        else:
            with SentinelClient(base_url) as client:
                client.login()
                detail = point.check(client)
    except AssertionError as exc:
        return Result(point.number, point.name, "FALLA", str(exc))
    except Exception as exc:  # noqa: BLE001 - a broken run is a failed point
        return Result(point.number, point.name, "FALLA", f"{type(exc).__name__}: {exc}")
    return Result(point.number, point.name, "PASA", detail)


def render_table(results: list[Result]) -> str:
    lines = [
        "| Point | What Felix tested | Result | Detail |",
        "|---|---|---|---|",
    ]
    for result in results:
        lines.append(f"| {result.number} | {result.name} | {result.status} | {result.detail} |")
    return "\n".join(lines)


def render_block(results: list[Result], base_url: str, manage_server: bool) -> str:
    setup = (
        "Setup: mock Gold, reference date 2026-06-17, customer `CUST-0001`, one new "
        "session per point"
    )
    if manage_server:
        setup += ", and one clean temporary SQLite file per point"
    setup += "."
    return "\n".join(
        [
            START,
            "## Felix replay (automated)",
            "",
            f"Run: `python3 scripts/felix_replay.py --base-url {base_url}`. {setup}",
            "The script repeats the ten points of the manual test of Felix on 2026-10-04.",
            "Points 4 and 8 depend on the model and stay out of scope for this change.",
            "",
            render_table(results),
            "",
            END,
        ]
    )


def write_report(block: str) -> None:
    text = REPORT.read_text(encoding="utf-8")
    if START in text and END in text:
        head = text[: text.index(START)]
        tail = text[text.index(END) + len(END):]
        text = head + block + tail
    else:
        anchor = "## How to add an entry"
        if anchor in text:
            text = text.replace(anchor, block + "\n\n" + anchor, 1)
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
    REPORT.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay the ten points of the manual test of Felix.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"service URL (default {DEFAULT_BASE_URL})")
    parser.add_argument(
        "--no-spawn",
        action="store_true",
        help="use the service at --base-url as is; start no local process",
    )
    args = parser.parse_args(argv)

    url = httpx.URL(args.base_url)
    loopback = url.host in ("127.0.0.1", "localhost", "::1")
    manage_server = loopback and not args.no_spawn
    port = url.port or 8002

    results = [run_point(point, args.base_url, manage_server, port) for point in POINTS]

    print(render_table(results))
    write_report(render_block(results, args.base_url, manage_server))

    failures = [result for result in results if result.status == "FALLA"]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
