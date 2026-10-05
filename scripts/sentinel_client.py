"""Reusable HTTP client for a running Sentinel service.

Other scripts import it: ``scripts/manual_test_replay.py`` for the manual test of
Felix, and the robustness and live-ops work for load and failure checks. It
speaks to the API over HTTP only, so the same client serves a local process and
a remote deployment.

Usage::

    from sentinel_client import SentinelClient

    with SentinelClient("http://127.0.0.1:8002") as client:
        client.login()
        reply = client.chat(message="hola")
        print(reply.status_code, reply.json())
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_LOGIN = "CUST-0001"
DEFAULT_PASSWORD = "Testpass-001"


class SentinelClient:
    """One cookie session against a running service.

    Each instance holds its own cookie jar, so two clients are two sessions,
    even for the same customer. Call ``login`` before a request that needs a
    session.
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def __enter__(self) -> "SentinelClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # --- session ----------------------------------------------------------

    def login(self, login: str = DEFAULT_LOGIN, password: str = DEFAULT_PASSWORD) -> httpx.Response:
        return self.post("/api/v1/auth/login", json={"login": login, "password": password})

    def logout(self) -> httpx.Response:
        return self.post("/api/v1/auth/logout")

    # --- service ----------------------------------------------------------

    def health(self) -> httpx.Response:
        return self.get("/api/v1/health")

    def reference_date(self) -> str:
        """The service reference date, from the health payload."""
        return str(self.health().json()["reference_date"])

    def chat(
        self,
        *,
        message: str | None = None,
        selected_reference: str | None = None,
        language: str | None = None,
    ) -> httpx.Response:
        body: dict[str, Any] = {}
        if message is not None:
            body["message"] = message
        if selected_reference is not None:
            body["selected_reference"] = selected_reference
        if language is not None:
            body["language"] = language
        return self.post("/api/v1/chat", json=body)

    def cases(self) -> httpx.Response:
        return self.get("/api/v1/disputes")

    # --- transport --------------------------------------------------------

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.post(path, **kwargs)
