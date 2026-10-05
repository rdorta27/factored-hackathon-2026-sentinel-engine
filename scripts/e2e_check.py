#!/usr/bin/env python3
"""Check a Sentinel service end to end, local or on the public link.

The check runs the three demo cases and the manual test replay, and it can
check the phone layout at 390 px. On a loopback base URL it starts a local app
with a clean SQLite file and the Gold mock. On a remote URL it uses the running
service and starts nothing.

Entry follows the service: when ``GET /api/v1/auth/demo`` answers 200, the
script enters by persona. When it answers 404, which is the public link, the
script enters by password. The judge logins and passwords come from the sheet
named by ``SENTINEL_E2E_CREDENTIALS_FILE``. The script never prints or logs a
password.

Usage, from the repository root::

    python3 scripts/e2e_check.py
    python3 scripts/e2e_check.py --base-url https://example.test
    python3 scripts/e2e_check.py --base-url https://example.test --access-check
    python3 scripts/e2e_check.py --no-phone

Exit code: 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "sentinel-ai-core"
DEMO_SCRIPTS = CORE_DIR / "eval" / "demo" / "pt-br.jsonl"
# The replay script name lives here once. docs-followups renamed it.
MANUAL_REPLAY = "scripts/manual_test_replay.py"
DEFAULT_BASE_URL = "http://127.0.0.1:8003"
REFERENCE_DATE = "2026-06-17"

# The documented fixture logins and their passwords. The public link turns them
# off; the access check proves that they fail there.
FIXTURE_PASSWORDS = {
    "CUST-0001": "Testpass-001",
    "CUST-0002": "Testpass-001",
    "CUST-0003": "Testpass-001",
    "ADV-0001": "Advisor-001",
}
# The one-click persona that logs in each demo customer.
PERSONA_BY_CUSTOMER = {
    "CUST-0001": "normal",
    "CUST-0002": "high-amount",
    "CUST-0003": "not-me",
}
# The role and the country that each judge login must report.
EXPECTED_IDENTITY = {
    "CUST-0001": ("customer", "MX"),
    "CUST-0002": ("customer", "CO"),
    "CUST-0003": ("customer", "AR"),
    "ADV-0001": ("advisor", "MX"),
}
# Cases that change the customer state: a dispute or a handoff ticket. A second
# run on a shared state can fail, so a remote run skips the duplicate.
STATEFUL_CASES = {"normal", "human"}
# The locales of the demo cases. es-MX is an es-419 variant.
DEMO_VARIANTS = ("es-MX", "pt-BR")

PHONE_VIEWPORT = {"width": 390, "height": 844}

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from sentinel_client import SentinelClient


@dataclass
class Result:
    name: str
    status: str
    detail: str


# --- helpers ----------------------------------------------------------------


def is_loopback(base_url: str) -> bool:
    host = httpx.URL(base_url).host
    return host in ("127.0.0.1", "localhost", "::1")


def demo_rows(variants: tuple[str, ...] = DEMO_VARIANTS) -> list[dict]:
    """The demo cases of the four variants, in file order."""
    rows = []
    for line in DEMO_SCRIPTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("block") == "demo" and row.get("variant") in variants:
            rows.append(row)
    return rows


def load_credentials(path: str | Path) -> dict[str, dict[str, str]]:
    """Read the judge sheet. Columns: login, role, password. No password is printed."""
    records: dict[str, dict[str, str]] = {}
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            login = (row.get("login") or "").strip()
            if login:
                records[login] = {"role": (row.get("role") or "").strip(), "password": row.get("password") or ""}
    return records


def personas_available(base_url: str) -> bool:
    try:
        return httpx.get(f"{base_url}/api/v1/auth/demo", timeout=15.0).status_code == 200
    except httpx.HTTPError:
        return False


def open_session(base_url: str, login: str, password: str, personas: bool) -> tuple[SentinelClient, httpx.Response]:
    """Enter by persona when the service offers it, otherwise by password."""
    client = SentinelClient(base_url)
    if personas:
        persona = PERSONA_BY_CUSTOMER.get(login)
        if persona is not None:
            response = client.post(f"/api/v1/auth/demo/{persona}")
            if response.status_code == 200:
                return client, response
    return client, client.login(login, password)


# --- local app --------------------------------------------------------------


def wait_for_health(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/api/v1/health", timeout=2.0).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"the service at {base_url} did not become healthy")


@contextmanager
def local_server(port: int, extra: dict[str, str] | None = None):
    """One local app with a clean SQLite file and the Gold mock."""
    with tempfile.TemporaryDirectory(prefix="e2e-check-") as folder:
        env = os.environ.copy()
        env.update(
            {
                "SENTINEL_STATE_BACKEND": "sqlite",
                "SENTINEL_DB_PATH": str(Path(folder) / "state.db"),
                "SENTINEL_GOLD_SOURCE": "mock",
                "SENTINEL_SECURE_COOKIES": "false",
                "SENTINEL_REFERENCE_DATE": REFERENCE_DATE,
                "SENTINEL_SESSION_SALT": secrets.token_hex(16),
                **(extra or {}),
            }
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=CORE_DIR,
            env=env,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            wait_for_health(base_url)
            yield base_url
        finally:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# --- the demo cases ---------------------------------------------------------


def replay_row(base_url: str, row: dict, personas: bool, credentials: dict[str, dict[str, str]] | None) -> Result:
    login = row["customer"]
    if credentials is not None:
        record = credentials.get(login)
        if record is None:
            return Result(row["id"], "FAIL", f"no judge credential for {login}")
        password = record["password"]
    else:
        password = FIXTURE_PASSWORDS[login]
    client, response = open_session(base_url, login, password, personas)
    try:
        if response.status_code != 200:
            return Result(row["id"], "FAIL", f"login {login} -> {response.status_code}")
        kinds = []
        for step in row["steps"]:
            reply = client.chat(**step)
            if reply.status_code != 200:
                return Result(row["id"], "FAIL", f"chat -> {reply.status_code}")
            kinds.append(reply.json().get("kind"))
        expected = row["expect"]
        if kinds == expected:
            return Result(row["id"], "PASS", f"{row['case']} {row['variant']}")
        return Result(row["id"], "FAIL", f"kinds {kinds} != {expected}")
    finally:
        client.close()


def run_demo_cases(base_url: str, *, spawn: bool, personas: bool, credentials: dict[str, dict[str, str]] | None) -> list[Result]:
    results: list[Result] = []
    seen: set[tuple[str, str]] = set()
    for row in demo_rows():
        key = (row["case"], row["customer"])
        if not spawn and row["case"] in STATEFUL_CASES and key in seen:
            results.append(Result(row["id"], "SKIP", "needs a clean state; run reset-state.sh first"))
            continue
        seen.add(key)
        if spawn:
            with local_server(httpx.URL(base_url).port or 8003) as url:
                results.append(replay_row(url, row, personas=personas, credentials=None))
        else:
            results.append(replay_row(base_url, row, personas=personas, credentials=credentials))
    return results


# --- the manual test replay -------------------------------------------------


def run_manual_replay(*, spawn: bool) -> Result:
    """Run scripts/manual_test_replay.py. It needs the fixture login, so it runs
    on a local app only: the public link turns the fixture login off."""
    if not spawn:
        return Result("manual test replay", "SKIP", "the fixture login is off on the link")
    script = REPO_ROOT / MANUAL_REPLAY
    completed = subprocess.run(
        [sys.executable, str(script), "--base-url", "http://127.0.0.1:8002"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return Result("manual test replay", "PASS", "ten points of the manual test")
    tail = (completed.stdout or completed.stderr).strip().splitlines()
    return Result("manual test replay", "FAIL", tail[-1] if tail else f"exit {completed.returncode}")


# --- the phone check --------------------------------------------------------


def evaluate_phone(metrics: dict[str, object]) -> tuple[bool, str]:
    """The pass or fail rule of the phone layout at 390 px."""
    problems = []
    if not metrics.get("no_horizontal_scroll"):
        problems.append("horizontal scroll")
    if not metrics.get("chat_form_visible"):
        problems.append("chat form hidden")
    if not metrics.get("build_line_visible"):
        problems.append("build line missing")
    if not metrics.get("judge_guide_present"):
        problems.append("judge guide missing")
    if metrics.get("judge_guide_open"):
        problems.append("judge guide open")
    if problems:
        return False, ", ".join(problems)
    return True, "390 px: no scroll, form, build line, closed guide"


def phone_metrics(page, width: int) -> dict[str, object]:
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    guide = page.locator('[data-testid="judge-guide"]')
    return {
        "no_horizontal_scroll": int(scroll_width) <= width,
        "chat_form_visible": page.locator("#chat-form").is_visible(),
        "build_line_visible": page.locator('[data-testid="build-info"]').is_visible(),
        "judge_guide_present": guide.count() > 0,
        "judge_guide_open": bool(guide.count()) and guide.first.evaluate("el => el.open === true"),
    }


def chrome_path() -> str:
    env = os.environ.get("SENTINEL_CHROME")
    if env:
        return env
    cache = Path.home() / ".cache" / "ms-playwright"
    for candidate in sorted(cache.glob("chromium-*/chrome-linux64/chrome"), reverse=True):
        if candidate.is_file():
            return str(candidate)
    import shutil

    found = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not found:
        raise RuntimeError("no Chromium found; set SENTINEL_CHROME")
    return found


def run_phone_check(base_url: str, *, spawn: bool, personas: bool, credentials: dict[str, dict[str, str]] | None) -> Result:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return Result("phone layout", "SKIP", "Playwright is not installed")

    login = "CUST-0001"
    password = credentials["CUST-0001"]["password"] if credentials is not None else FIXTURE_PASSWORDS[login]
    try:
        executable = chrome_path()
    except RuntimeError as exc:
        return Result("phone layout", "SKIP", str(exc))

    def check(url: str) -> Result:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=executable, args=["--no-sandbox"])
            try:
                context = browser.new_context(viewport=PHONE_VIEWPORT)
                page = context.new_page()
                page.goto(f"{url}/ui/", wait_until="networkidle")
                # The judge guide lives on the entry page and starts closed.
                page.wait_for_selector('[data-testid="judge-guide"]', timeout=15000)
                if personas:
                    page.click('[data-persona="normal"]')
                else:
                    page.locator("#password-login").evaluate("el => { el.open = true; }")
                    page.wait_for_selector("#login-user", state="visible")
                    page.fill("#login-user", login)
                    page.fill("#login-pass", password)
                    page.click('#login-form button[type="submit"]')
                page.wait_for_selector("#view-chat:not([hidden])", timeout=20000)
                page.wait_for_selector('[data-testid="build-info"]:not([hidden])', timeout=20000)
                page.wait_for_timeout(300)
                ok, detail = evaluate_phone(phone_metrics(page, PHONE_VIEWPORT["width"]))
                return Result("phone layout", "PASS" if ok else "FAIL", detail)
            finally:
                browser.close()

    if spawn:
        with local_server(httpx.URL(base_url).port or 8003, {"SENTINEL_DEMO_PERSONAS": "0" if not personas else "1"}) as url:
            return check(url)
    return check(base_url)


# --- the access check -------------------------------------------------------


def access_check(base_url: str, credentials: dict[str, dict[str, str]]) -> list[Result]:
    """Prove that the link has no passwordless entry and that the judge logins work."""
    results: list[Result] = []
    with httpx.Client(base_url=base_url, timeout=20.0) as http:
        response = http.get("/api/v1/auth/demo")
        results.append(
            Result(
                "persona route",
                "PASS" if response.status_code == 404 else "FAIL",
                f"GET /api/v1/auth/demo -> {response.status_code}",
            )
        )

    # One failed attempt for each login. The lockout lasts 15 minutes and the
    # judge logins share the four names, so a second attempt is not safe.
    for login, password in FIXTURE_PASSWORDS.items():
        with httpx.Client(base_url=base_url, timeout=20.0) as http:
            response = http.post("/api/v1/auth/login", json={"login": login, "password": password})
        results.append(
            Result(
                f"fixture password {login}",
                "PASS" if response.status_code == 401 else "FAIL",
                f"-> {response.status_code}",
            )
        )

    for login, record in credentials.items():
        expected = EXPECTED_IDENTITY.get(login)
        if expected is None:
            results.append(Result(f"judge login {login}", "FAIL", "unknown login"))
            continue
        with httpx.Client(base_url=base_url, timeout=20.0) as http:
            response = http.post("/api/v1/auth/login", json={"login": login, "password": record["password"]})
            if response.status_code != 200:
                results.append(Result(f"judge login {login}", "FAIL", f"-> {response.status_code}"))
                continue
            me = http.get("/api/v1/auth/me").json()
        got = (me.get("role"), me.get("country"))
        results.append(
            Result(
                f"judge login {login}",
                "PASS" if got == expected else "FAIL",
                f"role/country {got}",
            )
        )
    return results


# --- runner -----------------------------------------------------------------


def render(results: list[Result]) -> str:
    lines = ["| Check | Result | Detail |", "|---|---|---|"]
    for result in results:
        lines.append(f"| {result.name} | {result.status} | {result.detail} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Sentinel service end to end.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"service URL (default {DEFAULT_BASE_URL})")
    parser.add_argument("--access-check", action="store_true", help="check the entry rules and the judge logins only")
    parser.add_argument("--no-phone", action="store_true", help="skip the phone layout check")
    parser.add_argument("--no-manual", action="store_true", help="skip the manual test replay")
    args = parser.parse_args(argv)

    base_url = args.base_url.rstrip("/")
    loopback = is_loopback(base_url)

    credentials: dict[str, dict[str, str]] | None = None
    if not loopback:
        path = os.environ.get("SENTINEL_E2E_CREDENTIALS_FILE", "")
        if not path:
            print("error: set SENTINEL_E2E_CREDENTIALS_FILE for a remote base URL", file=sys.stderr)
            return 1
        credentials = load_credentials(path)

    if args.access_check:
        if loopback:
            local_credentials, users = _local_judge_files()
            with local_server(httpx.URL(base_url).port or 8003, _access_env(users)) as url:
                results = access_check(url, local_credentials)
        else:
            results = access_check(base_url, credentials or {})
        print(render(results))
        return 1 if any(r.status == "FAIL" for r in results) else 0

    personas = personas_available(base_url) if not loopback else False
    results = run_demo_cases(base_url, spawn=loopback, personas=personas, credentials=credentials)
    if not args.no_manual:
        results.append(run_manual_replay(spawn=loopback))
    if not args.no_phone:
        results.append(run_phone_check(base_url, spawn=loopback, personas=False, credentials=credentials))

    print(render(results))
    return 1 if any(r.status == "FAIL" for r in results) else 0


def _access_env(users: Path | None) -> dict[str, str]:
    env = {"SENTINEL_DEMO_PERSONAS": "0", "SENTINEL_DEMO_AUTH": "1"}
    if users is not None:
        env["SENTINEL_USERS_PATH"] = str(users)
    return env


def _local_judge_files() -> tuple[dict[str, dict[str, str]], Path]:
    """The judge sheet and the users file for a local access check.

    It uses the sheet named by SENTINEL_E2E_CREDENTIALS_FILE when both files
    exist. Otherwise it writes a fresh set in a temporary folder.
    """
    path = os.environ.get("SENTINEL_E2E_CREDENTIALS_FILE", "")
    if path:
        users = Path(path).with_name("users.json")
        if users.is_file():
            return load_credentials(path), users
    folder = Path(tempfile.mkdtemp(prefix="e2e-judge-"))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "make_judge_users.py"),
         "--users", str(folder / "users.json"), "--passwords", str(folder / "passwords.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return load_credentials(folder / "passwords.csv"), folder / "users.json"


if __name__ == "__main__":
    raise SystemExit(main())
