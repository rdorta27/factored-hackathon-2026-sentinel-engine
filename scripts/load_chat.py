"""Load-test POST /api/v1/chat on one process and report capacity numbers.

Drives a running app over HTTP with ``sentinel_client.py`` at increasing
request rates and prints one JSON summary per rate to standard output. It
never writes under ``evidence/``: the frozen run after the code freeze
does that.

Recorded answers: with ``--with-stub`` the script also starts a tiny stub
model server that replays one recorded router reply, and the spawned app
points at it, so the run measures the service instead of the provider. A
small live-model run uses the same script against an app pointed at the
real endpoint. ``--container`` spawns the app in Docker with the deployed
limits (0.5 vCPU, 1 GiB) instead of a local process.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sentinel_client import SentinelClient

RECORDED_CONTENT = '{"intent": "charge", "language": "es-419", "amount": null, "not_mine": false}'

SCRIPT = (
    {"message": "hola"},
    {"message": "no reconozco un cargo de ACME Store"},
    {"message": "quiero un préstamo"},
    {"message": "quiero hablar con una persona"},
)

AI_CORE_DIR = Path(__file__).resolve().parent.parent / "sentinel-ai-core"


class _StubHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = {
            "choices": [{"message": {"content": RECORDED_CONTENT}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        raw = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args: object) -> None:
        pass


def start_stub() -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


def wait_for_health(base_url: str, timeout_s: float = 60.0) -> None:
    import httpx

    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            if httpx.get(f"{base_url}/api/v1/health", timeout=2.0).status_code == 200:
                return
        except Exception:  # noqa: BLE001 - not up yet
            time.sleep(0.5)
    raise RuntimeError(f"app at {base_url} never became healthy")


def spawn_local(port: int, stub_port: int | None, llm_model: str) -> subprocess.Popen:
    env = {
        "SENTINEL_GOLD_SOURCE": "mock",
        "SENTINEL_STATE_BACKEND": "memory",
        "SENTINEL_SECURE_COOKIES": "false",
        "SENTINEL_LLM_PROMPT_VERSION": "v2",
    }
    if stub_port is not None:
        env.update(
            {
                "SENTINEL_LLM_BASE_URL": f"http://127.0.0.1:{stub_port}",
                "SENTINEL_LLM_API_KEY": "recorded",
                "SENTINEL_LLM_CHEAP_MODEL": llm_model,
                "SENTINEL_LLM_STRONG_MODEL": llm_model,
                "SENTINEL_LLM_DEFAULT_MODEL": llm_model,
            }
        )
    import os

    full_env = dict(os.environ)
    full_env.update(env)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        cwd=AI_CORE_DIR,
        env=full_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def spawn_container(image: str, port: int, stub_port: int | None) -> subprocess.Popen:
    cmd = [
        "docker", "run", "--rm",
        "--cpus=0.5", "--memory=1g",
        "--network=host",
        "-e", "SENTINEL_GOLD_SOURCE=mock",
        "-e", "SENTINEL_STATE_BACKEND=memory",
        "-e", "SENTINEL_SECURE_COOKIES=false",
    ]
    if stub_port is not None:
        cmd += ["-e", f"SENTINEL_LLM_BASE_URL=http://127.0.0.1:{stub_port}"]
    cmd += [image]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_rate(base_url: str, rate: float, duration_s: float, timeout: float) -> dict:
    latencies: list[float] = []
    errors = 0
    rejects = 0
    stop_at = time.perf_counter() + duration_s

    workers = max(1, min(16, int(rate) or 1))
    interval = workers / max(rate, 0.01)

    def worker(payloads: list[dict]) -> None:
        nonlocal errors, rejects
        with SentinelClient(base_url, timeout=timeout) as client:
            client.login()
            index = 0
            while time.perf_counter() < stop_at:
                started = time.perf_counter()
                try:
                    response = client.post("/api/v1/chat", json=payloads[index % len(payloads)])
                    latencies.append((time.perf_counter() - started) * 1000.0)
                    if response.status_code == 429:
                        rejects += 1
                    elif response.status_code != 200:
                        errors += 1
                except Exception:  # noqa: BLE001 - a failed turn is an error
                    errors += 1
                    latencies.append((time.perf_counter() - started) * 1000.0)
                index += 1
                time.sleep(max(0.0, interval))
    threads = [threading.Thread(target=worker, args=([dict(p) for p in SCRIPT],)) for _ in range(workers)]
    wall_start = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall_s = time.perf_counter() - wall_start
    total = len(latencies)
    return {
        "target_rps": rate,
        "achieved_rps": total / wall_s if wall_s > 0 else 0.0,
        "requests": total,
        "p50_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0.0),
        "errors": errors,
        "rejected_429": rejects,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Load-test one chat replica.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--rates", default="5,10,20")
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--spawn", action="store_true", help="launch a local app to drive")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--with-stub", action="store_true", help="replay recorded model answers")
    parser.add_argument("--llm-model", default="accounts/fireworks/models/glm-5p3-flash")
    parser.add_argument("--container", action="store_true", help="spawn in Docker with 0.5 vCPU and 1 GiB")
    parser.add_argument("--image", default="", help="app image for --container")
    args = parser.parse_args()

    stub_port: int | None = None
    server: HTTPServer | None = None
    app: subprocess.Popen | None = None
    base_url = args.base_url
    try:
        if args.with_stub:
            server, stub_port = start_stub()
        if args.spawn or args.container:
            if args.container and not args.image:
                parser.error("--container needs --image")
            base_url = f"http://127.0.0.1:{args.port}"
            app = (
                spawn_container(args.image, args.port, stub_port)
                if args.container
                else spawn_local(args.port, stub_port, args.llm_model)
            )
            wait_for_health(base_url)
        else:
            wait_for_health(base_url)
        results = []
        for raw in args.rates.split(","):
            rate = float(raw.strip())
            summary = run_rate(base_url, rate, args.duration, args.timeout)
            summary["stub"] = "recorded" if stub_port is not None else "live"
            summary["container"] = bool(args.container)
            results.append(summary)
            print(json.dumps(summary))
        return 0
    finally:
        if app is not None:
            app.terminate()
        if server is not None:
            server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
