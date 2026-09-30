from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UserRecord:
    customer_id: str
    country: str
    kdf: str
    salt_hex: str
    hash_hex: str
    role: str = "customer"


@dataclass(frozen=True)
class Session:
    token: str
    customer_id: str
    country: str
    created_at: datetime
    expires_at: datetime
    role: str = "customer"
