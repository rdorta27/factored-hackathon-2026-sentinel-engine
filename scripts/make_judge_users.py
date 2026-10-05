#!/usr/bin/env python3
"""Write the judge users file and its plain-password sheet. Prints no password.

One shared set for all judges (decision of 2026-10-05): three customer logins
(CUST-0001, CUST-0002, CUST-0003 of the persona map) and one advisor. The users
file holds salted hashes only and goes to the Azure Files share. The plain
passwords go to an ignored sheet that the owner pastes in the submission email.

    python3 scripts/make_judge_users.py
    python3 scripts/make_judge_users.py --users PATH --passwords PATH
"""

from __future__ import annotations

import argparse
import csv
import json
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "sentinel-ai-core"))

from app.session.security import hash_password  # noqa: E402

DEFAULT_USERS = REPO / "deploy" / "judge-users" / "users.json"
DEFAULT_PASSWORDS = REPO / "deploy" / "judge-users" / "passwords.csv"
KDF = "pbkdf2-sha256-600k"

# The persona map uses these three customers; one advisor reads the queue.
ACCOUNTS = (
    ("CUST-0001", "MX", "customer"),
    ("CUST-0002", "CO", "customer"),
    ("CUST-0003", "AR", "customer"),
    ("ADV-0001", "MX", "advisor"),
)


def random_password() -> str:
    return secrets.token_urlsafe(12)


def make_set() -> tuple[list[dict[str, str]], list[tuple[str, str, str]]]:
    users: list[dict[str, str]] = []
    sheet: list[tuple[str, str, str]] = []
    for login, country, role in ACCOUNTS:
        password = random_password()
        salt_hex = secrets.token_bytes(16).hex()
        users.append(
            {
                "login": login,
                "customer_id": login,
                "country": country,
                "role": role,
                "kdf": KDF,
                "salt_hex": salt_hex,
                "hash_hex": hash_password(password, salt_hex),
            }
        )
        sheet.append((login, role, password))
    return users, sheet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the judge users file and password sheet.")
    parser.add_argument("--users", default="", help="Users JSON. Empty uses deploy/judge-users/users.json.")
    parser.add_argument("--passwords", default="", help="Password sheet. Empty uses deploy/judge-users/passwords.csv.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    users_path = Path(args.users) if args.users else DEFAULT_USERS
    sheet_path = Path(args.passwords) if args.passwords else DEFAULT_PASSWORDS
    users, sheet = make_set()
    users_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    users_path.write_text(json.dumps({"users": users}, indent=2) + "\n", encoding="utf-8")
    with sheet_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("login", "role", "password"))
        writer.writerows(sheet)
    print(f"wrote {len(users)} judge logins")
    print(f"users file: {users_path}")
    print(f"passwords sheet: {sheet_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
