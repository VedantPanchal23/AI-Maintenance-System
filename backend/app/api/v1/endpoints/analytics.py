"""
Analytics & Dashboard Endpoints

GET /analytics/dashboard   — Dashboard summary (equipment health overview)
GET /analytics/trends      — Equipment risk trends over time
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.api.v1.schemas import DashboardSummary, EquipmentHealthSummary
from app.db.models.alert import Alert, AlertStatus
from app.db.models.equipment import Equipment, EquipmentStatus
from app.db.models.prediction import Prediction
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive dashboard summary.

    Returns equipment counts by status, active alerts,
    average risk scores, and per-equipment health summaries.
    """
    org_id = user.organization_id

    # Equipment by status
    result = await db.execute(
        select(
            Equipment.status,
            func.count(Equipment.id),
        )
        .where(
            Equipment.organization_id == org_id,
            Equipment.is_active == True,
        )
        .group_by(Equipment.status)
    )
    status_counts = {row[0].value if hasattr(row[0], 'value') else row[0]: row[1] for row in result.all()}

    total_equipment = sum(status_counts.values())
    operational = status_counts.get("operational", 0)
    warning = status_counts.get("warning", 0)
    critical = status_counts.get("critical", 0)
    maintenance = status_counts.get("maintenance", 0)

    # Active alerts count
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.organization_id == org_id,
            Alert.status == AlertStatus.ACTIVE,
        )
    )
    active_alerts = result.scalar() or 0

    # Average risk score
    result = await db.execute(
        select(func.avg(Equipment.risk_score)).where(
            Equipment.organization_id == org_id,
            Equipment.is_active == True,
        )
    )
    avg_risk = result.scalar() or 0.0

    # Per-equipment health summary
    result = await db.execute(
        select(Equipment)
        .where(
            Equipment.organization_id == org_id,
            Equipment.is_active == True,
        )
        .order_by(Equipment.risk_score.desc())
    )
    equipment_list = result.scalars().all()

    equipment_health = []
    for eq in equipment_list:
        # Count active alerts per equipment
        alert_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.equipment_id == eq.id,
                Alert.status == AlertStatus.ACTIVE,
            )
        )
        eq_alerts = alert_result.scalar() or 0

        equipment_health.append(
            EquipmentHealthSummary(
                equipment_id=eq.id,
                equipment_name=eq.name,
                equipment_type=eq.equipment_type.value if hasattr(eq.equipment_type, 'value') else eq.equipment_type,
                status=eq.status.value if hasattr(eq.status, 'value') else eq.status,
                risk_score=eq.risk_score,
                latest_prediction=eq.risk_score,
                active_alerts=eq_alerts,
                operating_hours=eq.operating_hours,
            )
        )

    return DashboardSummary(
        total_equipment=total_equipment,
        operational_count=operational,
        warning_count=warning,
        critical_count=critical,
        maintenance_count=maintenance,
        active_alerts=active_alerts,
        avg_risk_score=round(avg_risk, 4),
        equipment_health=equipment_health,
    )


@router.get("/equipment-health")
async def get_equipment_health(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get health summary for all equipment."""
    org_id = user.organization_id

    result = await db.execute(
        select(Equipment)
        .where(Equipment.organization_id == org_id, Equipment.is_active == True)
        .order_by(Equipment.risk_score.desc())
    )
    equipment_list = result.scalars().all()

    health = []
    for eq in equipment_list:
        alert_result = await db.execute(
            select(func.count(Alert.id)).where(
                Alert.equipment_id == eq.id,
                Alert.status == AlertStatus.ACTIVE,
            )
        )
        eq_alerts = alert_result.scalar() or 0

        health.append(
            EquipmentHealthSummary(
                equipment_id=eq.id,
                equipment_name=eq.name,
                equipment_type=eq.equipment_type.value if hasattr(eq.equipment_type, 'value') else eq.equipment_type,
                status=eq.status.value if hasattr(eq.status, 'value') else eq.status,
                risk_score=eq.risk_score,
                latest_prediction=eq.risk_score,
                active_alerts=eq_alerts,
                operating_hours=eq.operating_hours,
            )
        )

    return health


@router.get("/trends")
async def get_risk_trends(
    equipment_id: Optional[uuid.UUID] = Query(None, description="Equipment ID (optional)"),
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get risk score trends over time for equipment."""
    org_id = user.organization_id
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(
        Prediction.equipment_id,
        Prediction.timestamp,
        Prediction.failure_probability,
        Prediction.failure_type,
    ).where(
        Prediction.organization_id == org_id,
        Prediction.timestamp >= since,
    ).order_by(Prediction.timestamp.asc())

    if equipment_id:
        query = query.where(Prediction.equipment_id == equipment_id)

    result = await db.execute(query)
    rows = result.all()

    trends = [
        {
            "equipment_id": str(row[0]),
            "timestamp": row[1].isoformat(),
            "failure_probability": row[2],
            "failure_type": row[3].value if hasattr(row[3], 'value') else row[3],
        }
        for row in rows
    ]

    return {"trends": trends, "period_hours": hours, "count": len(trends)}
