"""
Audit Log Endpoints (Admin only)

GET /audit-logs — List audit log entries with filters
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_db
from app.api.v1.schemas import AuditLogListResponse, AuditLogResponse
from app.db.models.alert import AuditLog
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    action: str | None = Query(None, description="Filter by action type"),
    user_id: uuid.UUID | None = Query(None, description="Filter by user"),
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List audit log entries for the admin's organization."""
    base_q = select(AuditLog).where(
        AuditLog.organization_id == admin.organization_id
    )

    if action:
        base_q = base_q.where(AuditLog.action == action)
    if user_id:
        base_q = base_q.where(AuditLog.user_id == user_id)
    if resource_type:
        base_q = base_q.where(AuditLog.resource_type == resource_type)

    count_result = await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base_q.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    entries = result.scalars().all()

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=e.id,
                user_id=e.user_id,
                action=e.action,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                details=e.details,
                ip_address=e.ip_address,
                created_at=e.created_at,
            )
            for e in entries
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
