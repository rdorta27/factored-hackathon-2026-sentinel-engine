"""Scripted conversations against a running Sentinel service.

The script replays about 40 short conversations in the four interface variants
(es-MX, es-CO, es-AR, pt-BR). The cases come from the chat plan
([chat behaviour](../team/chat-behavior-plan.md)): the phrases of Felix, the
openers, a loan request and an amount in words. It uses the real model behind
the service.

For every reply the script checks:

* the expected reply kind;
* the expected message key (the opener or out-of-scope subtype, the charge
  status, the window rule);
* that an opener never hands off;
* that a model draft carries no unverified datum (no brace and no figure
  outside a verified value);
* the language of the model draft.

It writes the full conversations to a report block in
`team/chat-manual-tests.md`, between two markers.

Usage::

    python3 scripts/chat_transcripts.py
    python3 scripts/chat_transcripts.py --base-url http://127.0.0.1:8004 --no-spawn

On a loopback base URL the script starts one local uvicorn process with the
real model from `.env`. With `--no-spawn` it uses the running service.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinel_client import SentinelClient  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT / "sentinel-ai-core"
REPORT = REPO_ROOT / "team" / "chat-manual-tests.md"
DEFAULT_BASE_URL = "http://127.0.0.1:8004"
REFERENCE_DATE = "2026-06-17"
START = "<!-- chat-transcripts:start -->"
END = "<!-- chat-transcripts:end -->"

VARIANTS = ("es-MX", "es-CO", "es-AR", "pt-BR")
# The four variants share two answer languages: the three Spanish regionals
# answer in es-419, pt-BR answers in Portuguese.
LANGUAGE_OF = {"es-MX": "es-419", "es-CO": "es-419", "es-AR": "es-419", "pt-BR": "pt-BR"}

# Marks used only to spot a draft in the wrong language. A short draft with no
# mark in either list passes, like the server-side validator.
_PT_MARKS = ("não", "você", "voce", "obrigad", "bom dia", "cobrança", "cobranca", "atendente")
_ES_MARKS = ("gracias", "hola", "usted", "puedo", "quiero", "cargo", "cuéntame", "cuenteme")

_BRACE = re.compile(r"[{}]")
_DIGIT = re.compile(r"\d")


@dataclass(frozen=True)
class Step:
    """One customer message and what the reply must show."""

    messages: dict[str, str]
    kind: str | None = None
    key_prefix: str | None = None
    opener: bool = False


@dataclass
class Finding:
    case_id: str
    locale: str
    message: str
    status: str
    detail: str


@dataclass
class Transcript:
    case_id: str
    locale: str
    steps: list[tuple[str, dict]] = field(default_factory=list)


# --- the scripted cases -----------------------------------------------------


def _steps() -> list[Step]:
    return [
        Step(
            {
                "es-MX": "Hola, buenos días",
                "es-CO": "Buenos días, ¿cómo están?",
                "es-AR": "Hola, ¿cómo andás?",
                "pt-BR": "Olá, bom dia",
            },
            kind="text",
            key_prefix="opener.greeting",
            opener=True,
        ),
        Step(
            {
                "es-MX": "Muchas gracias por tu ayuda",
                "es-CO": "Gracias, muy amable",
                "es-AR": "Gracias, genio",
                "pt-BR": "Obrigado pela ajuda",
            },
            kind="text",
            key_prefix="opener.thanks",
            opener=True,
        ),
        Step(
            {
                "es-MX": "¿Eres un bot o una persona?",
                "es-CO": "¿Usted es un robot?",
                "es-AR": "¿Sos un bot?",
                "pt-BR": "Você é um robô ou uma pessoa?",
            },
            kind="text",
            key_prefix="opener.identity",
            opener=True,
        ),
        Step(
            {
                "es-MX": "¿En qué puedes ayudarme?",
                "es-CO": "¿Qué puedes hacer?",
                "es-AR": "¿Para qué servís?",
                "pt-BR": "O que você faz?",
            },
            kind="text",
            key_prefix="opener.help",
            opener=True,
        ),
        Step(
            {
                "es-MX": "Adiós, hasta luego",
                "es-CO": "Chau, hasta pronto",
                "es-AR": "Nos vemos, chau",
                "pt-BR": "Tchau, até logo",
            },
            kind="text",
            key_prefix="opener.goodbye",
            opener=True,
        ),
        Step(
            {
                "es-MX": "Hola, no reconozco el cargo de Cafe Central",
                "es-CO": "Buenos días, no reconozco un cargo en Cafe Central",
                "es-AR": "Hola, no reconozco el consumo de Cafe Central",
                "pt-BR": "Olá, não reconheço a cobrança da Cafe Central",
            },
            kind="confirm_box",
        ),
        Step(
            {
                "es-MX": "Quiero ver el estado de mi último cargo",
                "es-CO": "¿En qué estado está mi último cobro?",
                "es-AR": "¿Cómo va el estado de mi último consumo?",
                "pt-BR": "Quero ver o estado da minha última cobrança",
            },
            kind="explanation",
            key_prefix="charge.status",
        ),
        Step(
            {
                "es-MX": "Quiero un préstamo personal",
                "es-CO": "Necesito un préstamo de libre inversión",
                "es-AR": "Quiero pedir un préstamo",
                "pt-BR": "Quero um empréstimo pessoal",
            },
            kind="text",
            key_prefix="out_of_scope.loan",
        ),
        Step(
            {
                "es-MX": "¿Cuánta plata tengo en mi cuenta?",
                "es-CO": "¿Cuál es el saldo de mi cuenta?",
                "es-AR": "¿Cuánta guita tengo disponible?",
                "pt-BR": "Quanto dinheiro eu tenho na conta?",
            },
            kind="text",
            key_prefix="out_of_scope.balance",
        ),
        Step(
            {
                "es-MX": "Hay un cobro de mil pesos que no reconozco",
                "es-CO": "No reconozco un cobro de mil pesos",
                "es-AR": "No reconozco un consumo de mil pesos",
                "pt-BR": "Não reconheço uma cobrança de mil reais",
            },
            kind="confirm_box",
        ),
    ]


def _why_january() -> Step:
    return Step(
        {
            "es-MX": "¿Por qué no puedo reclamar el de enero?",
            "es-CO": "¿Por qué no puedo reclamar el de enero?",
            "es-AR": "¿Por qué no puedo reclamar el de enero?",
            "pt-BR": "Por que não posso contestar a de janeiro?",
        },
        kind="explanation",
        key_prefix="explanation.window.expired",
    )


# --- checks -----------------------------------------------------------------


def _draft_language(text: str, language: str) -> bool:
    lowered = text.lower()
    if language == "pt-BR":
        return not any(mark in lowered for mark in _ES_MARKS)
    return not any(mark in lowered for mark in _PT_MARKS)


def check_step(step: Step, reply: dict, language: str) -> list[Finding]:
    findings: list[Finding] = []
    kind = reply.get("kind")
    key = reply.get("message_key") or reply.get("reason_key") or ""
    if step.kind is not None and kind != step.kind:
        findings.append(Finding("", "", "", "FALLA", f"kind {kind}, wanted {step.kind}"))
    if step.key_prefix is not None and not key.startswith(step.key_prefix):
        findings.append(Finding("", "", "", "FALLA", f"key {key}, wanted {step.key_prefix}*"))
    if step.opener and kind == "handoff":
        findings.append(Finding("", "", "", "FALLA", "an opener handed off"))
    text = reply.get("text")
    if text:
        if _BRACE.search(text):
            findings.append(Finding("", "", "", "FALLA", "a draft kept a placeholder brace"))
        if _DIGIT.search(text) and not re.search(r"\d", key):
            # A figure in a draft is only allowed when it is a verified value.
            # The server fills values, so a figure here is reported for review.
            findings.append(Finding("", "", "", "REVISAR", "a draft carries a figure"))
        if not _draft_language(text, language):
            findings.append(Finding("", "", "", "FALLA", "a draft shows the wrong language"))
    return findings


def run_case(client: SentinelClient, case_id: str, step: Step, locale: str) -> tuple[Transcript, list[Finding]]:
    transcript = Transcript(case_id=case_id, locale=locale)
    findings: list[Finding] = []
    message = step.messages[locale]
    reply = client.chat(message=message, language=locale).json()
    transcript.steps.append((message, reply))
    for finding in check_step(step, reply, LANGUAGE_OF[locale]):
        finding.case_id = case_id
        finding.locale = locale
        finding.message = message
        findings.append(finding)
    return transcript, findings


def run_all(base_url: str) -> tuple[list[Transcript], list[Finding]]:
    transcripts: list[Transcript] = []
    findings: list[Finding] = []
    scenarios = [*_steps(), _why_january()]
    with SentinelClient(base_url) as client:
        client.login()
        for index, step in enumerate(scenarios, start=1):
            for locale in VARIANTS:
                # A fresh session per case, so one case cannot change the next.
                with SentinelClient(base_url) as fresh:
                    fresh.login()
                    case_id = f"CT-{index:02d}-{locale}"
                    if step.key_prefix == "explanation.window.expired":
                        fresh.chat(message="Hay un cobro de 2500 MXN en ACME Store", language=locale)
                    transcript, case_findings = run_case(fresh, case_id, step, locale)
                    transcripts.append(transcript)
                    findings.extend(case_findings)
    return transcripts, findings


# --- local server -----------------------------------------------------------


def wait_for_health(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/api/v1/health", timeout=2.0).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"the service at {base_url} did not become healthy")


@contextlib.contextmanager
def local_server(port: int):
    with tempfile.TemporaryDirectory(prefix="chat-transcripts-") as folder:
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


# --- report -----------------------------------------------------------------


def render(transcripts: list[Transcript], findings: list[Finding], base_url: str) -> str:
    lines = [
        START,
        "## Chat transcripts (automated)",
        "",
        f"Run: `python3 scripts/chat_transcripts.py --base-url {base_url}`. "
        f"Setup: mock Gold, reference date {REFERENCE_DATE}, customer `CUST-0001`, "
        "one new session per case, the real model.",
        "",
        f"{len(transcripts)} conversations, {len(findings)} findings.",
        "",
        "| Case | Variant | Customer | Reply |",
        "|---|---|---|---|",
    ]
    for transcript in transcripts:
        for message, reply in transcript.steps:
            shown = reply.get("text") or reply.get("message_key") or reply.get("kind", "")
            lines.append(f"| {transcript.case_id} | {transcript.locale} | {message} | {shown} |")
    if findings:
        lines += ["", "### Findings", "", "| Case | Variant | Status | Detail |", "|---|---|---|---|"]
        for finding in findings:
            lines.append(
                f"| {finding.case_id} | {finding.locale} | {finding.status} | {finding.detail} |"
            )
    else:
        lines += ["", "No finding. Every case matched its expected kind and key."]
    lines += ["", END]
    return "\n".join(lines)


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
    parser = argparse.ArgumentParser(description="Replay the scripted conversations against a service.")
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
    port = url.port or 8004

    if manage_server:
        with local_server(port) as base_url:
            transcripts, findings = run_all(base_url)
    else:
        transcripts, findings = run_all(args.base_url)

    block = render(transcripts, findings, args.base_url)
    print(block)
    write_report(block)
    return 1 if any(finding.status == "FALLA" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
