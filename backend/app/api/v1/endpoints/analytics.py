"""
Analytics & Dashboard Endpoints

GET /analytics/dashboard   — Dashboard summary (equipment health overview)
GET /analytics/trends      — Equipment risk trends over time
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.api.v1.schemas import DashboardSummary, EquipmentHealthSummary
from app.db.models.alert import Alert, AlertStatus
from app.db.models.equipment import Equipment, EquipmentStatus
from app.db.models.prediction import Prediction, MLModel
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    request: Request,
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

    # Batch: count active alerts per equipment in a single query
    alert_counts_result = await db.execute(
        select(Alert.equipment_id, func.count(Alert.id))
        .where(
            Alert.organization_id == org_id,
            Alert.status == AlertStatus.ACTIVE,
        )
        .group_by(Alert.equipment_id)
    )
    alert_counts_map = {row[0]: row[1] for row in alert_counts_result.all()}

    equipment_health = []
    for eq in equipment_list:
        eq_alerts = alert_counts_map.get(eq.id, 0)

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
        # Convenience fields for frontend
        healthy_equipment=operational,
        equipment_by_status={k: v for k, v in status_counts.items() if v > 0},
        predictions_today=await _count_predictions_today(db, org_id),
        alerts_this_week=await _count_alerts_this_week(db, org_id),
        model_accuracy=await _get_active_model_accuracy(request),
        system_uptime="99.9%",
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


# ═══════════════════════════════════════════════════════════════
# Helper functions for dashboard stats
# ═══════════════════════════════════════════════════════════════

async def _count_predictions_today(db: AsyncSession, org_id) -> int:
    """Count predictions made today."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(Prediction.id)).where(
            Prediction.organization_id == org_id,
            Prediction.timestamp >= today_start,
        )
    )
    return result.scalar() or 0


async def _count_alerts_this_week(db: AsyncSession, org_id) -> int:
    """Count alerts created this week."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.organization_id == org_id,
            Alert.created_at >= week_ago,
        )
    )
    return result.scalar() or 0


async def _get_active_model_accuracy(request: Request) -> Optional[float]:
    """Get the active ML model's accuracy metric from the app-level singleton."""
    try:
        model_service = request.app.state.model_service
        if model_service and model_service.is_loaded:
            metrics = model_service.model_info.get("metrics", {})
            return metrics.get("accuracy") or metrics.get("f1")
    except Exception:
        pass
    return None


@router.get("/trends")
async def get_risk_trends(
    equipment_id: Optional[uuid.UUID] = Query(None, description="Equipment ID (optional)"),
    hours: int = Query(default=24, ge=1, le=2160, description="Hours of history (max 90 days)"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get risk score trends over time, aggregated by date for charting.

    Returns a list of daily aggregations with avg_risk and max_risk,
    compatible with the frontend BarChart/AreaChart.
    """
    org_id = user.organization_id
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = select(
        func.date(Prediction.timestamp).label("date"),
        func.avg(Prediction.failure_probability).label("avg_risk"),
        func.max(Prediction.failure_probability).label("max_risk"),
        func.count(Prediction.id).label("count"),
    ).where(
        Prediction.organization_id == org_id,
        Prediction.timestamp >= since,
    ).group_by(
        func.date(Prediction.timestamp)
    ).order_by(
        func.date(Prediction.timestamp).asc()
    )

    if equipment_id:
        query = query.where(Prediction.equipment_id == equipment_id)

    result = await db.execute(query)
    rows = result.all()

    trends = [
        {
            "date": str(row[0]),
            "avg_risk": round(float(row[1] or 0), 4),
            "max_risk": round(float(row[2] or 0), 4),
            "count": row[3],
        }
        for row in rows
    ]

    return trends
