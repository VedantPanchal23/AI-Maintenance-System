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
from sqlalchemy.orm import selectinload

from app.api.v1.deps import PaginationDep, get_current_user, get_db
from app.api.v1.schemas import AlertListResponse, AlertResponse, AlertUpdateRequest
from app.core.exceptions import NotFoundException
from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_alert_response(alert: Alert) -> AlertResponse:
    """Build AlertResponse with computed fields from relationships."""
    data = AlertResponse.model_validate(alert)

    # Populate equipment name from loaded relationship
    if alert.equipment:
        data.equipment_name = alert.equipment.name

    # Populate failure details from linked prediction
    if hasattr(alert, "prediction") and alert.prediction:
        pred = alert.prediction
        data.failure_probability = pred.failure_probability
        ft = pred.failure_type
        data.failure_type = ft.value if hasattr(ft, "value") else ft

    return data


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
    base_filter = [Alert.organization_id == user.organization_id]

    if severity:
        base_filter.append(Alert.severity == AlertSeverity(severity))
    if status:
        base_filter.append(Alert.status == AlertStatus(status))
    if equipment_id:
        base_filter.append(Alert.equipment_id == equipment_id)

    count_query = select(func.count(Alert.id)).where(*base_filter)
    total = (await db.execute(count_query)).scalar()

    query = (
        select(Alert)
        .where(*base_filter)
        .options(selectinload(Alert.equipment), selectinload(Alert.prediction))
        .order_by(Alert.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return AlertListResponse(
        items=[_build_alert_response(a) for a in items],
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
        .options(selectinload(Alert.equipment), selectinload(Alert.prediction))
        .order_by(Alert.created_at.desc())
        .limit(100)
    )
    alerts = result.scalars().all()
    return [_build_alert_response(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert details by ID."""
    result = await db.execute(
        select(Alert)
        .where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
        .options(selectinload(Alert.equipment), selectinload(Alert.prediction))
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise NotFoundException("Alert", alert_id)

    return _build_alert_response(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    request: AlertUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update alert status (acknowledge, resolve, dismiss)."""
    result = await db.execute(
        select(Alert)
        .where(
            Alert.id == alert_id,
            Alert.organization_id == user.organization_id,
        )
        .options(selectinload(Alert.equipment), selectinload(Alert.prediction))
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

    return _build_alert_response(alert)
