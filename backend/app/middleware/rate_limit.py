"""
Rate Limiting Middleware

Uses slowapi (based on limits library) to enforce per-endpoint rate limits.
Protects against brute-force, abuse, and DDoS-style request floods.

Rate limits follow a tiered strategy:
  - Auth endpoints (login/register): Strict (5-10/min)
  - Write endpoints (POST/PUT/DELETE): Moderate (30-60/min)
  - Read endpoints (GET): Generous (120/min)
  - ML training: Very strict (3/hour)
"""

import logging
from typing import Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)


def _get_client_identifier(request: Request) -> str:
    """
    Extract client identifier for rate limiting.
    Uses JWT user ID if authenticated, otherwise falls back to IP.
    """
    # Try to get user from JWT (set by TenantMiddleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


# ── Limiter Instance ──────────────────────────────────────────
_settings = get_settings()

# Use Redis when available; fall back to in-memory for local dev without Redis
_storage_uri = _settings.REDIS_URL
try:
    import redis as _redis_lib
    _rc = _redis_lib.Redis.from_url(_storage_uri, socket_connect_timeout=1)
    _rc.ping()
    _rc.close()
except Exception:
    logger.warning("Redis not reachable at %s — rate limiter using in-memory storage", _storage_uri)
    _storage_uri = "memory://"

limiter = Limiter(
    key_func=_get_client_identifier,
    default_limits=["120/minute"],
    storage_uri=_storage_uri,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit violations."""
    logger.warning(
        "Rate limit exceeded: %s %s from %s",
        request.method,
        request.url.path,
        _get_client_identifier(request),
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": str(getattr(exc, "retry_after", 60)),
        },
    )
