"""Health reports one hash over the files that decide behavior."""

import re

from fastapi.testclient import TestClient

from app.build_info import bundle_files, bundle_hash
from app.main import create_app

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def test_bundle_covers_policy_examples_and_cutoffs() -> None:
    names = sorted(path.name for path in bundle_files())
    assert names == [
        "ar.yaml",
        "co.yaml",
        "examples_v2.json",
        "examples_v3.json",
        "mx.yaml",
        "router_config.json",
    ]


def test_bundle_hash_is_stable_hex() -> None:
    first, second = bundle_hash(), bundle_hash()
    assert first == second
    assert HEX64.match(first)


def test_health_reports_the_bundle_hash() -> None:
    body = TestClient(create_app()).get("/api/v1/health").json()
    assert body["bundle_hash"] == bundle_hash()


def test_a_changed_file_changes_the_hash(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import app.build_info as build_info

    before = bundle_hash()
    by_name = {path.name: path for path in bundle_files()}
    edited = tmp_path / "mx.yaml"
    edited.write_bytes(by_name["mx.yaml"].read_bytes() + b"\n# probe\n")
    monkeypatch.setattr(
        build_info,
        "bundle_files",
        lambda: [edited if path.name == "mx.yaml" else path for path in bundle_files()],
    )
    assert bundle_hash() != before
