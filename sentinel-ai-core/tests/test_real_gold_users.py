"""Users script: counts only, no identifiers on stdout, output ignored by git."""

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "write_real_gold_users.py"
AS_OF = "2026-06-17"

# Invented ids. The dataset shape is what the guard rejects; these must not
# appear on stdout.
IDS = (
    "CLI-MXELIG01",
    "CLI-MXHIGH01",
    "CLI-MXFRAUD1",
    "CLI-COELIG01",
    "CLI-COHIGH01",
    "CLI-COFRAUD1",
    "CLI-ARELIG01",
    "CLI-ARHIGH01",
    "CLI-ARFRAUD1",
    "CLI-FUTURE01",
    "TX-MX-ELIG",
    "TX-FUTURE",
)


def _row(reference: str, customer: str, country: str, amount: float, currency: str, day: str, score: float | None) -> tuple:
    return (reference, customer, amount, currency, "Tienda", day, "Approved", False, score, country)


def _write_view(path: Path) -> None:
    rows = [
        _row("TX-MX-ELIG", "CLI-MXELIG01", "México", 100.0, "MXN", "2026-06-01", None),
        _row("TX-MX-HIGH", "CLI-MXHIGH01", "México", 8000.0, "USD", "2026-06-01", 10.0),
        _row("TX-MX-FRAUD", "CLI-MXFRAUD1", "México", 100.0, "USD", "2026-06-01", 40.0),
        _row("TX-FUTURE", "CLI-FUTURE01", "México", 9000.0, "USD", "2026-06-18", 10.0),
        _row("TX-CO-ELIG", "CLI-COELIG01", "Colombia", 1000.0, "COP", "2026-06-01", 10.0),
        _row("TX-CO-HIGH", "CLI-COHIGH01", "Colombia", 40000000.0, "COP", "2026-06-01", 10.0),
        _row("TX-CO-FRAUD", "CLI-COFRAUD1", "Colombia", 1000.0, "COP", "2026-06-01", 40.0),
        _row("TX-AR-ELIG", "CLI-ARELIG01", "Argentina", 1000.0, "ARS", "2026-06-01", 10.0),
        _row("TX-AR-HIGH", "CLI-ARHIGH01", "Argentina", 3000000.0, "ARS", "2026-06-01", 10.0),
        _row("TX-AR-FRAUD", "CLI-ARFRAUD1", "Argentina", 1000.0, "ARS", "2026-06-01", 40.0),
    ]
    con = duckdb.connect(str(path))
    con.execute(
        """
        CREATE TABLE charges (
            transaction_id VARCHAR,
            customer_id VARCHAR,
            amount DOUBLE,
            currency VARCHAR,
            merchant_name VARCHAR,
            transaction_date DATE,
            transaction_status VARCHAR,
            is_disputed BOOLEAN,
            fraud_score DOUBLE,
            customer_country VARCHAR
        )
        """
    )
    con.executemany("INSERT INTO charges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute("CREATE VIEW v_service_dispute_eligible_transactions AS SELECT * FROM charges")
    con.close()


def test_script_prints_counts_and_no_ids(tmp_path: Path) -> None:
    db = tmp_path / "gold.duckdb"
    out = tmp_path / "users.json"
    _write_view(db)
    env = os.environ.copy()
    env["SENTINEL_USERS_PASSWORD"] = "Testpass-001"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--duckdb", str(db), "--out", str(out), "--as-of", AS_OF],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["MX 3", "CO 3", "AR 3"]
    leaked = result.stdout + result.stderr
    for identifier in IDS:
        assert identifier not in leaked
    assert str(db) not in leaked
    body = json.loads(out.read_text(encoding="utf-8"))
    assert [user["country"] for user in body["users"]] == ["MX", "MX", "MX", "CO", "CO", "CO", "AR", "AR", "AR"]
    assert {user["role"] for user in body["users"]} == {"customer"}
    assert "CLI-FUTURE01" not in out.read_text(encoding="utf-8")
    ignored = subprocess.run(
        ["git", "check-ignore", "-v", "data/real-gold-users.json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ignored.returncode == 0
    assert "data/" in ignored.stdout
