"""
Sensor Data Endpoints

POST /sensors/readings         — Ingest single sensor reading
POST /sensors/readings/batch   — Ingest batch of readings
GET  /sensors/readings         — Query readings for equipment
GET  /sensors/latest/{equip}   — Get latest reading for equipment
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import PaginationDep, get_current_user, get_db
from app.api.v1.schemas import SensorBatchCreate, SensorReadingCreate, SensorReadingResponse
from app.core.exceptions import NotFoundException
from app.db.models.equipment import Equipment
from app.db.models.sensor import SensorReading
from app.db.models.organization import User
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/readings", response_model=SensorReadingResponse, status_code=201)
async def create_sensor_reading(
    request: SensorReadingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single sensor reading."""
    # Verify equipment belongs to tenant
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == request.equipment_id,
            Equipment.organization_id == user.organization_id,
        )
    )
    equipment = result.scalar_one_or_none()
    if not equipment:
        raise NotFoundException("Equipment", request.equipment_id)

    reading = SensorReading(
        organization_id=user.organization_id,
        equipment_id=request.equipment_id,
        timestamp=request.timestamp or datetime.now(timezone.utc),
        air_temperature=request.air_temperature,
        process_temperature=request.process_temperature,
        rotational_speed=request.rotational_speed,
        torque=request.torque,
        tool_wear=request.tool_wear,
        vibration=request.vibration,
        power_consumption=request.power_consumption,
        pressure=request.pressure,
        humidity=request.humidity,
    )
    db.add(reading)
    await db.flush()

    return SensorReadingResponse.model_validate(reading)


@router.post("/readings/batch", status_code=201)
@limiter.limit("60/minute")
async def create_sensor_readings_batch(
    request: Request,
    body: SensorBatchCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a batch of sensor readings (up to 1000)."""
    # Collect unique equipment IDs and validate tenant ownership
    equipment_ids = {item.equipment_id for item in body.readings}
    for eq_id in equipment_ids:
        result = await db.execute(
            select(Equipment).where(
                Equipment.id == eq_id,
                Equipment.organization_id == user.organization_id,
            )
        )
        equipment = result.scalar_one_or_none()
        if not equipment:
            raise NotFoundException("Equipment", eq_id)

    readings = []
    for item in body.readings:
        reading = SensorReading(
            organization_id=user.organization_id,
            equipment_id=item.equipment_id,
            timestamp=item.timestamp or datetime.now(timezone.utc),
            air_temperature=item.air_temperature,
            process_temperature=item.process_temperature,
            rotational_speed=item.rotational_speed,
            torque=item.torque,
            tool_wear=item.tool_wear,
            vibration=item.vibration,
            power_consumption=item.power_consumption,
            pressure=item.pressure,
            humidity=item.humidity,
        )
        readings.append(reading)

    db.add_all(readings)
    await db.flush()

    logger.info("Ingested %d sensor readings", len(readings))
    return {"ingested": len(readings), "status": "success"}


@router.get("/readings", response_model=list[SensorReadingResponse])
async def get_sensor_readings(
    equipment_id: uuid.UUID = Query(..., description="Equipment ID"),
    start_time: Optional[datetime] = Query(None, description="Start timestamp"),
    end_time: Optional[datetime] = Query(None, description="End timestamp"),
    limit: int = Query(default=100, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Query sensor readings for a specific equipment."""
    query = select(SensorReading).where(
        SensorReading.equipment_id == equipment_id,
        SensorReading.organization_id == user.organization_id,
    )

    if start_time:
        query = query.where(SensorReading.timestamp >= start_time)
    if end_time:
        query = query.where(SensorReading.timestamp <= end_time)

    query = query.order_by(SensorReading.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    readings = result.scalars().all()

    return [SensorReadingResponse.model_validate(r) for r in readings]


@router.get("/latest/{equipment_id}", response_model=SensorReadingResponse)
async def get_latest_reading(
    equipment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent sensor reading for an equipment."""
    result = await db.execute(
        select(SensorReading)
        .where(
            SensorReading.equipment_id == equipment_id,
            SensorReading.organization_id == user.organization_id,
        )
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    )
    reading = result.scalar_one_or_none()

    if not reading:
        raise NotFoundException("Sensor reading for equipment", equipment_id)

    return SensorReadingResponse.model_validate(reading)
