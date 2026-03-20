"""
Maintenance Log CRUD Endpoints

POST   /maintenance              — Create maintenance log
GET    /maintenance              — List maintenance logs (with filters)
GET    /maintenance/{id}         — Get maintenance log detail
PUT    /maintenance/{id}         — Update maintenance log
DELETE /maintenance/{id}         — Delete maintenance log
"""

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_engineer_or_admin, get_current_user, get_db
from app.api.v1.schemas import (
    MaintenanceLogCreate,
    MaintenanceLogListResponse,
    MaintenanceLogResponse,
    MaintenanceLogUpdate,
)
from app.core.exceptions import ForbiddenException, NotFoundException
from app.db.models.alert import MaintenanceLog
from app.db.models.equipment import Equipment
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=MaintenanceLogResponse, status_code=201)
async def create_maintenance_log(
    body: MaintenanceLogCreate,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new maintenance log entry."""
    # Verify equipment belongs to tenant
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == body.equipment_id,
            Equipment.organization_id == user.organization_id,
        )
    )
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise NotFoundException("Equipment", body.equipment_id)

    log = MaintenanceLog(
        organization_id=user.organization_id,
        equipment_id=body.equipment_id,
        performed_by=user.id,
        maintenance_type=body.maintenance_type.value,
        description=body.description,
        status=body.status,
        priority=body.priority,
        started_at=body.started_at,
        completed_at=body.completed_at,
        cost=body.cost,
        downtime_hours=body.downtime_hours,
        parts_replaced=body.parts_replaced,
    )
    db.add(log)
    await db.flush()

    logger.info(
        "Maintenance log created: %s for equipment %s by %s",
        log.id, equipment.name, user.email,
    )

    return MaintenanceLogResponse(
        id=log.id,
        equipment_id=log.equipment_id,
        performed_by=log.performed_by,
        maintenance_type=log.maintenance_type,
        description=log.description,
        status=log.status,
        priority=log.priority,
        started_at=log.started_at,
        completed_at=log.completed_at,
        cost=log.cost,
        downtime_hours=log.downtime_hours,
        parts_replaced=log.parts_replaced,
        equipment_name=equipment.name,
        performer_name=user.full_name,
        created_at=log.created_at,
    )


@router.get("", response_model=MaintenanceLogListResponse)
async def list_maintenance_logs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    equipment_id: uuid.UUID | None = Query(None),
    maintenance_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List maintenance logs for the user's organization."""
    base_q = select(MaintenanceLog).where(
        MaintenanceLog.organization_id == user.organization_id
    )

    if equipment_id:
        base_q = base_q.where(MaintenanceLog.equipment_id == equipment_id)
    if maintenance_type:
        base_q = base_q.where(MaintenanceLog.maintenance_type == maintenance_type)

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await db.execute(
        base_q.order_by(MaintenanceLog.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()

    # Resolve equipment names and performer names
    eq_ids = {l.equipment_id for l in logs}
    user_ids = {l.performed_by for l in logs if l.performed_by}

    eq_map = {}
    if eq_ids:
        eq_result = await db.execute(
            select(Equipment.id, Equipment.name).where(Equipment.id.in_(eq_ids))
        )
        eq_map = dict(eq_result.all())

    user_map = {}
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.full_name).where(User.id.in_(user_ids))
        )
        user_map = dict(user_result.all())

    return MaintenanceLogListResponse(
        items=[
            MaintenanceLogResponse(
                id=l.id,
                equipment_id=l.equipment_id,
                performed_by=l.performed_by,
                maintenance_type=l.maintenance_type,
                description=l.description,
                status=l.status,
                priority=l.priority,
                started_at=l.started_at,
                completed_at=l.completed_at,
                cost=l.cost,
                downtime_hours=l.downtime_hours,
                parts_replaced=l.parts_replaced,
                equipment_name=eq_map.get(l.equipment_id),
                performer_name=user_map.get(l.performed_by),
                created_at=l.created_at,
            )
            for l in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=MaintenanceLogResponse)
async def get_maintenance_log(
    log_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific maintenance log entry."""
    result = await db.execute(
        select(MaintenanceLog).where(
            MaintenanceLog.id == log_id,
            MaintenanceLog.organization_id == user.organization_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise NotFoundException("MaintenanceLog", log_id)

    # Resolve names
    eq_result = await db.execute(
        select(Equipment.name).where(Equipment.id == log.equipment_id)
    )
    eq_name = eq_result.scalar_one_or_none()

    performer_name = None
    if log.performed_by:
        u_result = await db.execute(
            select(User.full_name).where(User.id == log.performed_by)
        )
        performer_name = u_result.scalar_one_or_none()

    return MaintenanceLogResponse(
        id=log.id,
        equipment_id=log.equipment_id,
        performed_by=log.performed_by,
        maintenance_type=log.maintenance_type,
        description=log.description,
        status=log.status,
        priority=log.priority,
        started_at=log.started_at,
        completed_at=log.completed_at,
        cost=log.cost,
        downtime_hours=log.downtime_hours,
        parts_replaced=log.parts_replaced,
        equipment_name=eq_name,
        performer_name=performer_name,
        created_at=log.created_at,
    )


@router.put("/{log_id}", response_model=MaintenanceLogResponse)
async def update_maintenance_log(
    log_id: uuid.UUID,
    body: MaintenanceLogUpdate,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a maintenance log. Only the original performer or admin can update."""
    result = await db.execute(
        select(MaintenanceLog).where(
            MaintenanceLog.id == log_id,
            MaintenanceLog.organization_id == user.organization_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise NotFoundException("MaintenanceLog", log_id)

    if log.performed_by != user.id and user.role.value != "admin":
        raise ForbiddenException("Only the original performer or an admin can update this log")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(log, field, value)

    await db.flush()

    eq_result = await db.execute(
        select(Equipment.name).where(Equipment.id == log.equipment_id)
    )
    eq_name = eq_result.scalar_one_or_none()

    return MaintenanceLogResponse(
        id=log.id,
        equipment_id=log.equipment_id,
        performed_by=log.performed_by,
        maintenance_type=log.maintenance_type,
        description=log.description,
        status=log.status,
        priority=log.priority,
        started_at=log.started_at,
        completed_at=log.completed_at,
        cost=log.cost,
        downtime_hours=log.downtime_hours,
        parts_replaced=log.parts_replaced,
        equipment_name=eq_name,
        performer_name=user.full_name,
        created_at=log.created_at,
    )


@router.delete("/{log_id}", status_code=204)
async def delete_maintenance_log(
    log_id: uuid.UUID,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a maintenance log. Only the original performer or admin can delete."""
    result = await db.execute(
        select(MaintenanceLog).where(
            MaintenanceLog.id == log_id,
            MaintenanceLog.organization_id == user.organization_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise NotFoundException("MaintenanceLog", log_id)

    if log.performed_by != user.id and user.role.value != "admin":
        raise ForbiddenException("Only the original performer or an admin can delete this log")

    await db.delete(log)
    await db.flush()

    logger.info("Maintenance log %s deleted by %s", log_id, user.email)
