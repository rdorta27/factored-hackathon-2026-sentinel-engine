"""Password verification with stdlib PBKDF2 and constant-time comparison."""

import hashlib
import hmac

ITERATIONS = 600_000

# Verifier used when the customer id is unknown, so the timing and the
# error shape stay identical to a wrong-password failure.
DUMMY_SALT_HEX = "00" * 16
DUMMY_HASH_HEX = "00" * 32


def hash_password(password: str, salt_hex: str) -> str:
    """Derive the hex verifier for a password and salt."""
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """Compare a password against its stored verifier in constant time."""
    candidate = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate, expected_hash_hex)
