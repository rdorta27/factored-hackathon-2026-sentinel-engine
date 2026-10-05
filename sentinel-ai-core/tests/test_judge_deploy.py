"""Deploy pieces for judge access: upload script, flags and documentation."""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
UPLOAD = REPO / "deploy" / "azure" / "upload-users.sh"
DEPLOY = REPO / "deploy" / "azure" / "deploy.sh"
README = REPO / "deploy" / "azure" / "README.md"


def test_upload_users_dry_run_prints_the_commands_and_no_key() -> None:
    result = subprocess.run(
        ["bash", str(UPLOAD), "--dry-run"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "az storage account keys list" in result.stdout
    assert "az storage file upload" in result.stdout
    assert "users.json" in result.stdout
    assert "--account-key <storage-key>" in result.stdout


def test_deploy_sets_the_users_path_and_turns_the_personas_off() -> None:
    text = DEPLOY.read_text(encoding="utf-8")
    assert 'SENTINEL_USERS_PATH="$MOUNT_PATH/users.json"' in text
    assert "SENTINEL_DEMO_PERSONAS=0" in text


def test_readme_documents_the_upload_and_the_flags() -> None:
    text = README.read_text(encoding="utf-8")
    assert "upload-users.sh" in text
    assert "SENTINEL_USERS_PATH" in text
    assert "SENTINEL_DEMO_PERSONAS" in text
