"""Strict request/response schemas. Extra fields are always rejected."""

from pydantic import BaseModel, ConfigDict, Field

CUSTOMER_ID_PATTERN = r"^[A-Za-z0-9\-]{4,32}$"


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    customer_id: str = Field(pattern=CUSTOMER_ID_PATTERN)
    password: str = Field(min_length=1, max_length=128)


class MeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str
