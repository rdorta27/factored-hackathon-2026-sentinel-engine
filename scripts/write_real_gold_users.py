#!/usr/bin/env python3
"""Write a gitignored users file for real Gold customers. Prints counts only.

Per country (MX, CO, AR): one customer with a recent approved charge below both
handoff thresholds, one above the high-amount threshold, and one above the fraud
score. Identifiers, rows and the data location never reach stdout or a tracked file.

    SENTINEL_USERS_PASSWORD=... python3 scripts/write_real_gold_users.py
    python3 scripts/write_real_gold_users.py --duckdb PATH --out PATH
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sentinel-ai-core"))

from app.policy.load import load_country  # noqa: E402
from app.session.security import hash_password  # noqa: E402

VIEW = "v_service_dispute_eligible_transactions"
COUNTRY_NAMES = {
    "MX": ("México", "Mexico", "MX"),
    "CO": ("Colombia", "CO"),
    "AR": ("Argentina", "AR"),
}
SLOTS = ("eligible", "high_amount", "fraud_score")
DEFAULT_AS_OF = "2026-06-17"
PASSWORD_ENV = "SENTINEL_USERS_PASSWORD"
KDF = "pbkdf2-sha256-600k"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a gitignored real-Gold users file.")
    parser.add_argument("--duckdb", default="", help="Gold file. Empty uses SENTINEL_GOLD_DUCKDB or the repository default.")
    parser.add_argument("--out", default="", help="Users JSON. Empty uses data/real-gold-users.json.")
    parser.add_argument("--as-of", default="", help="Reference date. Empty uses SENTINEL_REFERENCE_DATE or 2026-06-17.")
    return parser.parse_args()


def _gold_path(explicit: str) -> Path | None:
    if explicit:
        return Path(explicit)
    from app.services.gold_service import gold_duckdb_path

    return gold_duckdb_path()


def _as_of(explicit: str) -> date:
    import os

    raw = explicit or os.environ.get("SENTINEL_REFERENCE_DATE", "").strip() or DEFAULT_AS_OF
    return date.fromisoformat(raw)


def _limits(policy, name: str) -> dict[str, float]:  # type: ignore[no-untyped-def]
    threshold = getattr(policy, name)
    return {code: float(limit) for code, limit in threshold.values}


def _pick(con, country: str, as_of: date, window_start: date, where: str, params: list) -> str | None:  # type: ignore[no-untyped-def]
    names = COUNTRY_NAMES[country]
    placeholders = ", ".join("?" for _ in names)
    sql = f"""
        SELECT customer_id
        FROM {VIEW}
        WHERE customer_country IN ({placeholders})
          AND lower(transaction_status) = 'approved'
          AND CAST(transaction_date AS DATE) <= CAST(? AS DATE)
          AND CAST(transaction_date AS DATE) >= CAST(? AS DATE)
          AND {where}
        LIMIT 1
    """
    row = con.execute(sql, [*names, as_of.isoformat(), window_start.isoformat(), *params]).fetchone()
    return None if row is None else str(row[0])


def _under_limits(limits: dict[str, float], column: str, null_ok: bool) -> tuple[str, list]:
    """A charge in a currency with no limit, or at or under that currency's limit."""
    if not limits:
        return "1 = 1", []
    codes = list(limits)
    parts = ["currency NOT IN (" + ", ".join("?" for _ in codes) + ")"]
    params: list = list(codes)
    for currency, limit in limits.items():
        compare = f"({column} IS NULL OR {column} <= ?)" if null_ok else f"{column} <= ?"
        parts.append(f"(currency = ? AND {compare})")
        params.extend([currency, limit])
    return "(" + " OR ".join(parts) + ")", params


def _slot_where(policy, slot: str, taken: list[str]) -> tuple[str, list]:  # type: ignore[no-untyped-def]
    high = _limits(policy, "high_amount")
    fraud = _limits(policy, "fraud_score")
    params: list = []
    if slot == "eligible":
        amount_clause, amount_params = _under_limits(high, "amount", null_ok=False)
        fraud_clause, fraud_params = _under_limits(fraud, "fraud_score", null_ok=True)
        params.extend(amount_params)
        params.extend(fraud_params)
        where = "COALESCE(is_disputed, false) = false AND " + amount_clause + " AND " + fraud_clause
    elif slot == "high_amount":
        parts = []
        for currency, limit in high.items():
            fraud_limit = fraud.get(currency)
            fraud_clause = ""
            local = [currency, limit]
            if fraud_limit is not None:
                fraud_clause = " AND (fraud_score IS NULL OR fraud_score <= ?)"
                local.append(fraud_limit)
            parts.append(f"(currency = ? AND amount > ?{fraud_clause})")
            params.extend(local)
        where = "(" + " OR ".join(parts) + ")" if parts else "1 = 0"
    else:
        parts = []
        for currency, limit in fraud.items():
            high_limit = high.get(currency)
            high_clause = ""
            local = [currency, limit]
            if high_limit is not None:
                high_clause = " AND amount <= ?"
                local.append(high_limit)
            parts.append(f"(currency = ? AND fraud_score > ?{high_clause})")
            params.extend(local)
        where = "(" + " OR ".join(parts) + ")" if parts else "1 = 0"
    if taken:
        where += " AND customer_id NOT IN (" + ", ".join("?" for _ in taken) + ")"
        params.extend(taken)
    return where, params


def _user(login: str, customer_id: str, country: str, password: str) -> dict[str, str]:
    salt_hex = secrets.token_bytes(16).hex()
    return {
        "login": login,
        "customer_id": customer_id,
        "country": country,
        "role": "customer",
        "kdf": KDF,
        "salt_hex": salt_hex,
        "hash_hex": hash_password(password, salt_hex),
    }


def main() -> int:
    import os

    args = _parse_args()
    password = os.environ.get(PASSWORD_ENV, "")
    if not password:
        print(f"{PASSWORD_ENV} is required", file=sys.stderr)
        return 2
    path = _gold_path(args.duckdb)
    if path is None or not path.is_file():
        print("gold file is not readable", file=sys.stderr)
        return 1
    as_of = _as_of(args.as_of)
    out = Path(args.out) if args.out else ROOT / "data" / "real-gold-users.json"
    users: list[dict[str, str]] = []
    try:
        con = duckdb.connect(str(path), read_only=True)
    except Exception:
        print("gold file is not readable", file=sys.stderr)
        return 1
    try:
        for country in ("MX", "CO", "AR"):
            policy = load_country(country)
            if policy is None:
                print(f"{country} 0", file=sys.stdout)
                print("policy is missing", file=sys.stderr)
                return 1
            window_start = as_of - timedelta(days=policy.window_days)
            taken: list[str] = []
            found = 0
            for slot in SLOTS:
                where, params = _slot_where(policy, slot, taken)
                customer_id = _pick(con, country, as_of, window_start, where, params)
                if customer_id is None:
                    continue
                taken.append(customer_id)
                login = f"{country.lower()}-{slot.replace('_', '-')}"
                users.append(_user(login, customer_id, country, password))
                found += 1
            print(f"{country} {found}")
            if found != len(SLOTS):
                return 1
    except Exception:
        print("gold read failed", file=sys.stderr)
        return 1
    finally:
        con.close()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"users": users}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
