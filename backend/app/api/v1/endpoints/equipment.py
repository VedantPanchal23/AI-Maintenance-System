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
from app.core.exceptions import NotFoundException
from app.db.models.equipment import Equipment, EquipmentStatus, EquipmentType
from app.db.models.organization import User

logger = logging.getLogger(__name__)
router = APIRouter()


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
        query = query.where(Equipment.status == EquipmentStatus(status))
    if equipment_type:
        query = query.where(Equipment.equipment_type == EquipmentType(equipment_type))
    if search:
        query = query.where(Equipment.name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.offset(pagination.offset).limit(pagination.page_size)
    query = query.order_by(Equipment.name)

    result = await db.execute(query)
    items = result.scalars().all()

    return EquipmentListResponse(
        items=[EquipmentResponse.model_validate(eq) for eq in items],
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
    return EquipmentResponse.model_validate(equipment)


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

    return EquipmentResponse.model_validate(equipment)


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
    return EquipmentResponse.model_validate(equipment)


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
