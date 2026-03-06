"""
Equipment Management Endpoints

GET    /equipment           — List equipment for tenant
POST   /equipment           — Create equipment
GET    /equipment/{id}      — Get equipment details
PUT    /equipment/{id}      — Update equipment
DELETE /equipment/{id}      — Soft-delete equipment
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import PaginationDep, get_current_engineer_or_admin, get_current_user, get_db, get_tenant_id
from app.api.v1.schemas import (
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentResponse,
    EquipmentUpdate,
)
from app.core.risk import compute_risk_level as _compute_risk_level
from app.core.exceptions import NotFoundException
from app.db.models.alert import MaintenanceLog
from app.db.models.equipment import Equipment, EquipmentStatus, EquipmentType
from app.db.models.organization import User
from app.db.models.prediction import Prediction
from app.db.models.sensor import SensorReading

logger = logging.getLogger(__name__)
router = APIRouter()


async def _enrich_equipment(db: AsyncSession, eq: Equipment) -> EquipmentResponse:
    """Build EquipmentResponse with computed fields from related tables."""
    data = EquipmentResponse.model_validate(eq)

    # Latest prediction → risk score & level
    pred_result = await db.execute(
        select(Prediction.failure_probability, Prediction.failure_type)
        .where(Prediction.equipment_id == eq.id)
        .order_by(Prediction.timestamp.desc())
        .limit(1)
    )
    pred_row = pred_result.first()
    if pred_row:
        prob = pred_row[0]
        data.latest_risk_score = round(prob, 4)
        data.latest_risk_level = _compute_risk_level(prob)

    # Latest sensor reading timestamp
    sr_result = await db.execute(
        select(SensorReading.timestamp)
        .where(SensorReading.equipment_id == eq.id)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )
    sr_row = sr_result.scalar_one_or_none()
    if sr_row:
        data.last_reading_at = sr_row

    # Latest maintenance log
    ml_result = await db.execute(
        select(func.max(MaintenanceLog.completed_at))
        .where(MaintenanceLog.equipment_id == eq.id)
    )
    ml_time = ml_result.scalar_one_or_none()
    if ml_time:
        data.last_maintenance_at = ml_time

    return data


async def _enrich_equipment_batch(db: AsyncSession, equipment_list: list) -> list[EquipmentResponse]:
    """Batch-enrich equipment list to avoid N+1 queries."""
    if not equipment_list:
        return []

    eq_ids = [eq.id for eq in equipment_list]

    # Batch: latest prediction per equipment (window function)
    from sqlalchemy import and_
    pred_sub = (
        select(
            Prediction.equipment_id,
            Prediction.failure_probability,
            func.row_number().over(
                partition_by=Prediction.equipment_id,
                order_by=Prediction.timestamp.desc()
            ).label("rn")
        )
        .where(Prediction.equipment_id.in_(eq_ids))
        .subquery()
    )
    pred_result = await db.execute(
        select(pred_sub.c.equipment_id, pred_sub.c.failure_probability)
        .where(pred_sub.c.rn == 1)
    )
    pred_map = {row[0]: row[1] for row in pred_result.all()}

    # Batch: latest sensor reading timestamp per equipment
    sr_sub = (
        select(
            SensorReading.equipment_id,
            func.max(SensorReading.timestamp).label("latest_ts")
        )
        .where(SensorReading.equipment_id.in_(eq_ids))
        .group_by(SensorReading.equipment_id)
    )
    sr_result = await db.execute(sr_sub)
    sr_map = {row[0]: row[1] for row in sr_result.all()}

    # Batch: latest maintenance log per equipment
    ml_sub = (
        select(
            MaintenanceLog.equipment_id,
            func.max(MaintenanceLog.completed_at).label("latest_maint")
        )
        .where(MaintenanceLog.equipment_id.in_(eq_ids))
        .group_by(MaintenanceLog.equipment_id)
    )
    ml_result = await db.execute(ml_sub)
    ml_map = {row[0]: row[1] for row in ml_result.all()}

    # Build responses
    enriched = []
    for eq in equipment_list:
        data = EquipmentResponse.model_validate(eq)
        prob = pred_map.get(eq.id)
        if prob is not None:
            data.latest_risk_score = round(prob, 4)
            data.latest_risk_level = _compute_risk_level(prob)
        sr_ts = sr_map.get(eq.id)
        if sr_ts:
            data.last_reading_at = sr_ts
        ml_ts = ml_map.get(eq.id)
        if ml_ts:
            data.last_maintenance_at = ml_ts
        enriched.append(data)

    return enriched


@router.get("", response_model=EquipmentListResponse)
async def list_equipment(
    pagination: PaginationDep = Depends(),
    status: str | None = Query(None, description="Filter by status"),
    equipment_type: str | None = Query(None, description="Filter by type"),
    search: str | None = Query(None, description="Search by name"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all equipment for the current tenant."""
    org_id = user.organization_id

    query = select(Equipment).where(
        Equipment.organization_id == org_id,
        Equipment.is_active == True,
    )

    # Apply filters
    if status:
        try:
            query = query.where(Equipment.status == EquipmentStatus(status))
        except ValueError:
            from app.core.exceptions import BadRequestException
            raise BadRequestException(f"Invalid status: {status}")
    if equipment_type:
        try:
            query = query.where(Equipment.equipment_type == EquipmentType(equipment_type))
        except ValueError:
            from app.core.exceptions import BadRequestException
            raise BadRequestException(f"Invalid equipment_type: {equipment_type}")
    if search:
        # Escape LIKE wildcards to prevent LIKE-injection
        safe_search = search.replace("%", "\\%").replace("_", "\\_")
        query = query.where(Equipment.name.ilike(f"%{safe_search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.order_by(Equipment.name)

    result = await db.execute(query)
    items = result.scalars().all()

    enriched = await _enrich_equipment_batch(db, items)

    return EquipmentListResponse(
        items=enriched,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    request: EquipmentCreate,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new equipment record."""
    equipment = Equipment(
        organization_id=user.organization_id,
        name=request.name,
        equipment_type=EquipmentType(request.equipment_type.value),
        location=request.location,
        manufacturer=request.manufacturer,
        model_number=request.model_number,
        serial_number=request.serial_number,
        installation_date=request.installation_date,
        rated_power_kw=request.rated_power_kw,
        max_rpm=request.max_rpm,
        notes=request.notes,
    )
    db.add(equipment)
    await db.flush()

    logger.info("Created equipment: %s (id=%s)", equipment.name, equipment.id)
    return await _enrich_equipment(db, equipment)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get equipment details by ID."""
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == equipment_id,
            Equipment.organization_id == user.organization_id,
        )
    )
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise NotFoundException("Equipment", equipment_id)

    return await _enrich_equipment(db, equipment)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: uuid.UUID,
    request: EquipmentUpdate,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update equipment details."""
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == equipment_id,
            Equipment.organization_id == user.organization_id,
        )
    )
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise NotFoundException("Equipment", equipment_id)

    # Apply partial update (exclude_unset keeps only fields the client sent)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value is not None:
            setattr(equipment, field, EquipmentStatus(value.value))
        else:
            setattr(equipment, field, value)

    await db.flush()
    logger.info("Updated equipment: %s", equipment_id)
    return await _enrich_equipment(db, equipment)


@router.delete("/{equipment_id}", status_code=204)
async def delete_equipment(
    equipment_id: uuid.UUID,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete equipment (marks inactive)."""
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == equipment_id,
            Equipment.organization_id == user.organization_id,
        )
    )
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise NotFoundException("Equipment", equipment_id)

    equipment.is_active = False
    await db.flush()
    logger.info("Soft-deleted equipment: %s", equipment_id)
