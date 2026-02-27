"""
Alert Management Endpoints

GET   /alerts              — List alerts for tenant
GET   /alerts/{id}         — Get alert details
PUT   /alerts/{id}         — Update alert status (acknowledge/resolve)
GET   /alerts/active       — List active alerts only
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import PaginationDep, get_current_user, get_db
from app.api.v1.schemas import AlertListResponse, AlertResponse, AlertUpdateRequest
from app.core.exceptions import NotFoundException
from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    pagination: PaginationDep = Depends(),
    severity: str | None = Query(None, description="Filter by severity"),
    status: str | None = Query(None, description="Filter by status"),
    equipment_id: uuid.UUID | None = Query(None, description="Filter by equipment"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all alerts for the current tenant."""
    query = select(Alert).where(Alert.organization_id == user.organization_id)

    if severity:
        query = query.where(Alert.severity == AlertSeverity(severity))
    if status:
        query = query.where(Alert.status == AlertStatus(status))
    if equipment_id:
        query = query.where(Alert.equipment_id == equipment_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Alert.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/active", response_model=list[AlertResponse])
async def list_active_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active (unresolved) alerts."""
    result = await db.execute(
        select(Alert)
        .where(
            Alert.organization_id == user.organization_id,
            Alert.status == AlertStatus.ACTIVE,
        )
        .order_by(Alert.created_at.desc())
        .limit(100)
    )
    alerts = result.scalars().all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert details by ID."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException("Alert", alert_id)

    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    request: AlertUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update alert status (acknowledge, resolve, dismiss)."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException("Alert", alert_id)

    now = datetime.now(timezone.utc)

    alert.status = AlertStatus(request.status.value)

    if request.status == "acknowledged":
        alert.acknowledged_by = user.id
        alert.acknowledged_at = now
    elif request.status in ("resolved", "dismissed"):
        alert.resolved_at = now
        if request.resolution_notes:
            alert.resolution_notes = request.resolution_notes

    await db.flush()
    logger.info("Alert %s updated to %s", alert_id, request.status)

    return AlertResponse.model_validate(alert)
