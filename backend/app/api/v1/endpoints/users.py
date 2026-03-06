"""
User Management Endpoints (Admin only)

GET    /users              — List users in organization
GET    /users/{id}         — Get user details
PUT    /users/{id}/role    — Change user role
PUT    /users/{id}/status  — Activate/deactivate user
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_current_user, get_db
from app.api.v1.schemas import AlertPreferencesResponse, AlertPreferencesUpdate, UserResponse
from app.core.exceptions import BadRequestException, NotFoundException
from app.db.models.organization import User, UserRole
from app.services.audit import record_audit

logger = logging.getLogger(__name__)
router = APIRouter()


class RoleUpdateRequest(BaseModel):
    role: str  # admin | engineer | viewer


class StatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the admin's organization."""
    result = await db.execute(
        select(User)
        .where(User.organization_id == admin.organization_id)
        .order_by(User.created_at)
    )
    users = result.scalars().all()

    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value.lower() if hasattr(u.role, "value") else u.role,
            organization_id=u.organization_id,
            is_active=u.is_active,
            last_login=u.last_login,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get user details by ID."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == admin.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", user_id)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value.lower() if hasattr(user.role, "value") else user.role,
        organization_id=user.organization_id,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: uuid.UUID,
    body: RoleUpdateRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role (admin only)."""
    try:
        new_role = UserRole(body.role.upper())
    except ValueError:
        raise BadRequestException(f"Invalid role: {body.role}. Must be admin, engineer, or viewer.")

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == admin.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", user_id)

    if user.id == admin.id:
        raise BadRequestException("Cannot change your own role")

    user.role = new_role
    await db.flush()

    await record_audit(
        db,
        user_id=admin.id,
        organization_id=admin.organization_id,
        action="user.role_change",
        resource_type="user",
        resource_id=str(user_id),
        details={"new_role": new_role.value},
        ip_address=request.client.host if request.client else None,
    )

    logger.info("User %s role changed to %s by admin %s", user_id, new_role.value, admin.id)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value.lower() if hasattr(user.role, "value") else user.role,
        organization_id=user.organization_id,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.put("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    body: StatusUpdateRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a user (admin only)."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.organization_id == admin.organization_id,
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User", user_id)

    if user.id == admin.id:
        raise BadRequestException("Cannot deactivate yourself")

    user.is_active = body.is_active
    await db.flush()

    await record_audit(
        db,
        user_id=admin.id,
        organization_id=admin.organization_id,
        action="user.status_change",
        resource_type="user",
        resource_id=str(user_id),
        details={"is_active": body.is_active},
        ip_address=request.client.host if request.client else None,
    )

    logger.info("User %s status changed to is_active=%s by admin %s", user_id, body.is_active, admin.id)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value.lower() if hasattr(user.role, "value") else user.role,
        organization_id=user.organization_id,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
    )


# ═══════════════════════════════════════════════════════════════
# Alert Preferences (self-service)
# ═══════════════════════════════════════════════════════════════

@router.get("/me/alert-preferences", response_model=AlertPreferencesResponse)
async def get_my_alert_preferences(
    user: User = Depends(get_current_user),
):
    """Get the current user's alert notification preferences."""
    prefs = user.alert_preferences or {"email_enabled": True, "severities": ["critical", "high"]}
    return AlertPreferencesResponse(
        notification_email=user.notification_email,
        email_enabled=prefs.get("email_enabled", True),
        severities=prefs.get("severities", ["critical", "high"]),
    )


@router.put("/me/alert-preferences", response_model=AlertPreferencesResponse)
async def update_my_alert_preferences(
    body: AlertPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's alert notification preferences."""
    if body.notification_email is not None:
        user.notification_email = body.notification_email

    user.alert_preferences = {
        "email_enabled": body.email_enabled,
        "severities": body.severities,
    }
    await db.flush()

    return AlertPreferencesResponse(
        notification_email=user.notification_email,
        email_enabled=body.email_enabled,
        severities=body.severities,
    )
