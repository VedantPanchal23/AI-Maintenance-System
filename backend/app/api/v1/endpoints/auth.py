"""
Authentication Endpoints

POST /auth/login      — Authenticate and receive tokens
POST /auth/register   — Register new user + organization
POST /auth/refresh    — Refresh access token
GET  /auth/me         — Get current user profile
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.api.v1.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.config import get_settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.organization import Organization, User, UserRole
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and organization."""

    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    if result.scalar_one_or_none():
        raise ConflictException(f"Email '{body.email}' is already registered")

    # Create organization (ensure unique slug even on case-insensitive collision)
    import re
    base_slug = re.sub(r"[^a-z0-9]+", "-", body.organization_name.lower()).strip("-")[:90]
    org_slug = base_slug
    suffix = 0
    while True:
        result = await db.execute(
            select(Organization).where(Organization.slug == org_slug)
        )
        existing_org = result.scalar_one_or_none()
        if not existing_org:
            break
        # Slug taken — if the existing org has the exact same name, reuse it;
        # otherwise create a uniquely-suffixed slug for the new org.
        if existing_org.name.lower() == body.organization_name.lower():
            break
        suffix += 1
        org_slug = f"{base_slug}-{suffix}"

    org = existing_org if (existing_org and existing_org.name.lower() == body.organization_name.lower()) else None
    if not org:
        org = Organization(
            name=body.organization_name,
            slug=org_slug,
        )
        db.add(org)
        await db.flush()

    # Create user
    user = User(
        organization_id=org.id,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole(body.role),
    )
    db.add(user)
    await db.flush()

    logger.info("New user registered: %s (org=%s)", user.email, org.name)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        organization_id=user.organization_id,
        organization_name=org.name,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""

    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    tokens = create_token_pair(
        user_id=str(user.id),
        organization_id=str(user.organization_id),
        role=user.role.value,
    )

    logger.info("User logged in: %s", user.email)

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""

    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found")

    tokens = create_token_pair(
        user_id=str(user.id),
        organization_id=str(user.organization_id),
        role=user.role.value,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user profile."""

    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        organization_id=current_user.organization_id,
        organization_name=org.name if org else None,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
    )
