import hashlib
import hmac

ITERATIONS = 600_000
DUMMY_SALT_HEX = "00" * 16
DUMMY_HASH_HEX = "00" * 32


def hash_password(password: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    candidate = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate, expected_hash_hex)
