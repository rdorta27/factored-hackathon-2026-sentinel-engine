"""Judge users script: hashes only in the users file, no password on stdout."""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from app.session.security import verify_password

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "make_judge_users.py"
LOGINS = ("CUST-0001", "CUST-0002", "CUST-0003", "ADV-0001")


def test_script_writes_hashes_and_keeps_passwords_out_of_the_users_file(tmp_path: Path) -> None:
    users = tmp_path / "users.json"
    sheet = tmp_path / "passwords.csv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--users", str(users), "--passwords", str(sheet)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rows = list(csv.DictReader(sheet.read_text(encoding="utf-8").splitlines()))
    assert [row["login"] for row in rows] == list(LOGINS)
    assert {row["role"] for row in rows} == {"customer", "advisor"}
    for row in rows:
        assert row["password"] not in result.stdout
    users_text = users.read_text(encoding="utf-8")
    body = json.loads(users_text)
    assert [user["login"] for user in body["users"]] == list(LOGINS)
    assert [user["country"] for user in body["users"]] == ["MX", "CO", "AR", "MX"]
    by_login = {user["login"]: user for user in body["users"]}
    for row in rows:
        assert row["password"] not in users_text, row["login"]
        user = by_login[row["login"]]
        assert user["hash_hex"] != row["password"]
        assert verify_password(row["password"], user["salt_hex"], user["hash_hex"])


def test_default_paths_are_git_ignored() -> None:
    for path in ("deploy/judge-users/users.json", "deploy/judge-users/passwords.csv"):
        ignored = subprocess.run(
            ["git", "check-ignore", "-v", path],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ignored.returncode == 0, path
