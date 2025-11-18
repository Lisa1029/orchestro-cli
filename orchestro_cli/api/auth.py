"""Authentication and authorization middleware."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel


# API key storage (in-memory for MVP, would use database in production)
api_keys: Dict[str, "APIKey"] = {}


class APIKey(BaseModel):
    """API key model."""

    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    rate_limit: int = 100  # requests per minute
    usage_count: int = 0
    last_used: Optional[datetime] = None


# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


def generate_api_key(name: str, expires_days: Optional[int] = None) -> str:
    """
    Generate a new API key.

    Args:
        name: Descriptive name for the key
        expires_days: Number of days until expiration (None = never)

    Returns:
        Generated API key string
    """
    key = f"orchestro_{secrets.token_urlsafe(32)}"

    expires_at = None
    if expires_days:
        expires_at = datetime.now() + timedelta(days=expires_days)

    api_keys[key] = APIKey(
        key=key,
        name=name,
        created_at=datetime.now(),
        expires_at=expires_at
    )

    return key


def validate_api_key(
    api_key_header_value: Optional[str] = Security(api_key_header),
    api_key_query_value: Optional[str] = Security(api_key_query),
) -> APIKey:
    """
    Validate API key from header or query parameter.

    Args:
        api_key_header_value: API key from X-API-Key header
        api_key_query_value: API key from api_key query parameter

    Returns:
        Valid APIKey object

    Raises:
        HTTPException: If API key is invalid or expired
    """
    # Get key from header or query
    key = api_key_header_value or api_key_query_value

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via X-API-Key header or api_key query parameter."
        )

    # Check if key exists
    if key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    api_key_obj = api_keys[key]

    # Check if key is active
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive"
        )

    # Check if key is expired
    if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )

    # Update usage
    api_key_obj.usage_count += 1
    api_key_obj.last_used = datetime.now()

    return api_key_obj


def check_rate_limit(api_key: APIKey) -> bool:
    """
    Check if API key has exceeded rate limit.

    Args:
        api_key: API key to check

    Returns:
        True if within rate limit, False otherwise
    """
    # Simple rate limit (would use Redis in production)
    # For now, just return True (no rate limiting in MVP)
    return True


# Initialize with a development key
DEV_API_KEY = generate_api_key("development", expires_days=365)
print(f"🔑 Development API Key: {DEV_API_KEY}")
