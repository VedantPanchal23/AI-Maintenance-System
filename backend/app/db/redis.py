"""
Async Redis client for the application.

Used for:
- Account lockout tracking (failed login attempts)
- JWT token blocklist (revoked tokens)
- Rate limiting (via slowapi)
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Return the global async Redis client (or None if unavailable)."""
    return _redis


async def init_redis() -> Optional[aioredis.Redis]:
    """Initialize the async Redis connection pool. Call once at startup."""
    global _redis
    settings = get_settings()
    try:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await _redis.ping()
        logger.info("Redis connected: %s", settings.REDIS_URL)
        return _redis
    except Exception as e:
        logger.warning("Redis unavailable (%s) — lockout and token blocklist disabled", e)
        _redis = None
        return None


async def close_redis() -> None:
    """Close the Redis connection pool. Call at shutdown."""
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")


# ═══════════════════════════════════════════════════════════════
# Account Lockout Helpers
# ═══════════════════════════════════════════════════════════════

LOCKOUT_PREFIX = "lockout:"
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 15 * 60  # 15 minutes


async def record_failed_login(email: str) -> int:
    """Increment failed login counter. Returns new count."""
    if not _redis:
        return 0
    key = f"{LOCKOUT_PREFIX}{email}"
    count = await _redis.incr(key)
    if count == 1:
        await _redis.expire(key, LOCKOUT_DURATION_SECONDS)
    return count


async def is_account_locked(email: str) -> bool:
    """Check if account is locked due to too many failures."""
    if not _redis:
        return False
    key = f"{LOCKOUT_PREFIX}{email}"
    count = await _redis.get(key)
    return count is not None and int(count) >= MAX_FAILED_ATTEMPTS


async def clear_failed_logins(email: str) -> None:
    """Clear failed login counter on successful login."""
    if not _redis:
        return
    await _redis.delete(f"{LOCKOUT_PREFIX}{email}")


async def get_lockout_ttl(email: str) -> int:
    """Get remaining lockout time in seconds."""
    if not _redis:
        return 0
    ttl = await _redis.ttl(f"{LOCKOUT_PREFIX}{email}")
    return max(ttl, 0)


# ═══════════════════════════════════════════════════════════════
# JWT Token Blocklist
# ═══════════════════════════════════════════════════════════════

BLOCKLIST_PREFIX = "blocklist:"


async def add_token_to_blocklist(jti: str, expires_in: int) -> None:
    """Add a token's JTI to the blocklist with a TTL matching its expiry."""
    if not _redis:
        return
    await _redis.setex(f"{BLOCKLIST_PREFIX}{jti}", expires_in, "1")


async def is_token_blocklisted(jti: str) -> bool:
    """Check if a token has been revoked."""
    if not _redis:
        return False
    return await _redis.exists(f"{BLOCKLIST_PREFIX}{jti}") > 0
