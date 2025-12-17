"""
Token usage logging schema and constants
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

TokenAction = Literal[
    "convert_start",
    "convert_success",
    "convert_fail",
    "download",
    "api_call",
]


class TokenLog(BaseModel):
    user_id: int = Field(..., description="Internal user id")
    username: Optional[str] = Field(None, description="Username snapshot")
    action: TokenAction = Field(..., description="What triggered token usage")
    tokens: int = Field(..., ge=0, description="Token amount (>=0)")
    balance_before: Optional[int] = Field(None, ge=0)
    balance_after: Optional[int] = Field(None, ge=0)
    request_id: Optional[str] = Field(None, description="Correlation id for a request")
    meta: Optional[dict] = Field(default_factory=dict, description="Optional extra info")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


DEFAULT_TOKEN_COSTS = {
    "convert_start": 0,
    "convert_success": 1,  # baseline unit; adjust to your pricing
    "convert_fail": 0,
    "download": 0,
    "api_call": 0,
}


def make_token_log(
    *,
    user_id: int,
    username: Optional[str],
    action: TokenAction,
    tokens: int,
    balance_before: Optional[int] = None,
    balance_after: Optional[int] = None,
    request_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> TokenLog:
    return TokenLog(
        user_id=user_id,
        username=username,
        action=action,
        tokens=tokens,
        balance_before=balance_before,
        balance_after=balance_after,
        request_id=request_id,
        meta=meta or {},
    )




