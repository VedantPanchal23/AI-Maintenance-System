"""
FastAPI Dependencies — Reusable dependency injection functions.

Handles authentication, database sessions, tenant context, and pagination.
"""

import uuid
import logging
from typing import Optional

from fastapi import Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.redis import is_token_blocklisted
from app.db.session import get_db
from app.db.models.organization import User, UserRole

logger = logging.getLogger(__name__)
settings = get_settings()

security_scheme = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════
# Authentication Dependencies
# ═══════════════════════════════════════════════════════════════

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT token, return authenticated user."""
    if not credentials:
        raise UnauthorizedException("Missing authentication token")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    # Check token blocklist (revoked tokens)
    jti = payload.get("jti")
    if jti and await is_token_blocklisted(jti):
        raise UnauthorizedException("Token has been revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        raise UnauthorizedException("Invalid token payload")

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_uuid, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found or deactivated")

    return user


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require admin role."""
    if user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin access required")
    return user


async def get_current_engineer_or_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require engineer or admin role."""
    if user.role not in (UserRole.ADMIN, UserRole.ENGINEER):
        raise ForbiddenException("Engineer or admin access required")
    return user


# ═══════════════════════════════════════════════════════════════
# Tenant Context
# ═══════════════════════════════════════════════════════════════

def get_tenant_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    """Extract organization_id from authenticated user for tenant scoping."""
    return user.organization_id


# ═══════════════════════════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════════════════════════

class PaginationDep:
    """Pagination parameters from query string."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
