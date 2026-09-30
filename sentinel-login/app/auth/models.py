"""Shared domain records for authentication."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserRecord:
    """One test customer with a stored password verifier (never plaintext)."""

    customer_id: str
    kdf: str
    salt_hex: str
    hash_hex: str
    role: str = "customer"


@dataclass(frozen=True)
class Session:
    """An authenticated server-side session. The token is an opaque key."""

    token: str
    customer_id: str
    created_at: datetime
    expires_at: datetime
    role: str = "customer"
