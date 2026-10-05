"""No synchronous work runs directly in an async function (REQ-0026).

Business routes are sync ``def`` and run in the server threadpool (see
``app/db/session.py``). The only ``async def`` functions are the tracing
middleware and the offloaded Gold readers. This test fails if a new async
function calls a blocking API directly instead of entering the threadpool
with ``asyncio.to_thread``.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

# Dotted call names that block the event loop when awaited directly.
_BLOCKING = frozenset(
    {
        "duckdb.connect",
        "duckdb.query",
        "sqlite3.connect",
        "httpx.Client",
        "httpx.get",
        "httpx.post",
        "httpx.put",
        "httpx.delete",
        "httpx.request",
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.request",
        "requests.Session",
        "open",
        "read_text",
        "write_text",
        "read_bytes",
        "write_bytes",
        "os.open",
        "os.read",
        "time.sleep",
    }
)


def _dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return None if base is None else f"{base}.{node.attr}"
    return None


def _blocking_in(node: ast.AST, *, inside_threadpool: bool = False) -> set[str]:
    """Blocking call names under ``node``, ignoring ``asyncio.to_thread`` bodies."""
    found: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        name = _dotted(child.func)
        if name in ("asyncio.to_thread", "run_in_threadpool"):
            continue
        if name in _BLOCKING:
            found.add(name)
    return found


def _async_functions() -> list[tuple[str, str, set[str]]]:
    """(file, qualified name, blocking calls) for every ``async def`` in app/."""
    report = []
    for path in sorted(APP_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                report.append((str(path.relative_to(APP_DIR.parent)), node.name, _blocking_in(node)))
    return report


def test_async_functions_exist() -> None:
    names = {name for _, name, _ in _async_functions()}
    assert names, "expected at least one async function in app/"
    assert "trace_middleware" in names


def test_no_blocking_call_inside_async_functions() -> None:
    offenders = [(where, name, sorted(calls)) for where, name, calls in _async_functions() if calls]
    assert not offenders, f"blocking calls inside async functions (use asyncio.to_thread): {offenders}"


def test_known_async_functions_are_named() -> None:
    """Guard the inventory: a new async route must be a deliberate choice."""
    names = {name for _, name, _ in _async_functions()}
    assert names == {"trace_middleware", "fetch_transactions_for_customer", "fetch_transaction"}
