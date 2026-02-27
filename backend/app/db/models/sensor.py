"""
Sensor Reading Model

Time-series sensor data from equipment.
Designed for high-volume inserts with time-based indexing.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class SensorReading(Base, TenantMixin):
    """Individual sensor reading from equipment."""

    __tablename__ = "sensor_readings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # ── Sensor Values ──
    air_temperature: Mapped[float] = mapped_column(Float, nullable=True)
    process_temperature: Mapped[float] = mapped_column(Float, nullable=True)
    rotational_speed: Mapped[int] = mapped_column(Integer, nullable=True)  # RPM
    torque: Mapped[float] = mapped_column(Float, nullable=True)  # Nm
    tool_wear: Mapped[int] = mapped_column(Integer, nullable=True)  # minutes
    vibration: Mapped[float] = mapped_column(Float, nullable=True)  # mm/s
    power_consumption: Mapped[float] = mapped_column(Float, nullable=True)  # kW
    pressure: Mapped[float] = mapped_column(Float, nullable=True)  # bar
    humidity: Mapped[float] = mapped_column(Float, nullable=True)  # %

    # Metadata
    quality_flag: Mapped[str] = mapped_column(String(20), default="good")  # good | suspect | bad

    # Relationships
    equipment = relationship("Equipment", back_populates="sensor_readings")

    __table_args__ = (
        Index("ix_sensor_readings_equip_time", "equipment_id", "timestamp"),
        Index("ix_sensor_readings_org_time", "organization_id", "timestamp"),
    )
