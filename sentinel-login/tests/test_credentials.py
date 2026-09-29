"""Unit tests for credential verification, including unknown-user parity."""

from app.auth import security
from app.auth.security import DUMMY_HASH_HEX, DUMMY_SALT_HEX


def test_correct_password_verifies() -> None:
    assert security.verify_password(
        "Testpass-001",
        "45b5e0773a37c30a74c8c55db9127254",
        "e5a817cf2a81c01de1a96490d82c0170dacc1e25206f5e659dad1818d9ca62af",
    )


def test_wrong_password_fails() -> None:
    assert not security.verify_password(
        "Wrongpass-999",
        "45b5e0773a37c30a74c8c55db9127254",
        "e5a817cf2a81c01de1a96490d82c0170dacc1e25206f5e659dad1818d9ca62af",
    )


def test_unknown_user_dummy_verifier_always_fails() -> None:
    assert not security.verify_password("anything", DUMMY_SALT_HEX, DUMMY_HASH_HEX)


def test_comparison_uses_constant_time_compare() -> None:
    import inspect

    source = inspect.getsource(security.verify_password)
    assert "compare_digest" in source
    assert " == " not in source
