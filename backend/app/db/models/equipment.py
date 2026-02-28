"""
Equipment Model

Represents physical machines — compressors, pumps, motors, HVAC.
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class EquipmentType(str, PyEnum):
    AIR_COMPRESSOR = "air_compressor"
    PUMP = "pump"
    ELECTRIC_MOTOR = "electric_motor"
    HVAC_CHILLER = "hvac_chiller"
    CNC_MILL = "cnc_mill"
    HYDRAULIC_PRESS = "hydraulic_press"
    INJECTION_MOLDER = "injection_molder"
    CONVEYOR = "conveyor"
    COMPRESSOR = "compressor"
    MOTOR = "motor"


class EquipmentStatus(str, PyEnum):
    OPERATIONAL = "operational"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class Equipment(Base, TimestampMixin, TenantMixin):
    """Physical equipment registry per tenant."""

    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Enum(EquipmentType), nullable=False, index=True
    )
    status: Mapped[EquipmentStatus] = mapped_column(
        Enum(EquipmentStatus), default=EquipmentStatus.OPERATIONAL
    )
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    manufacturer: Mapped[str] = mapped_column(String(255), nullable=True)
    model_number: Mapped[str] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=True, unique=True)
    installation_date: Mapped[str] = mapped_column(String(20), nullable=True)

    # Operating parameters
    rated_power_kw: Mapped[float] = mapped_column(Float, nullable=True)
    max_rpm: Mapped[int] = mapped_column(Integer, nullable=True)
    operating_hours: Mapped[float] = mapped_column(Float, default=0.0)

    # Current risk score (cached from latest prediction)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="equipment")
    sensor_readings = relationship(
        "SensorReading", back_populates="equipment", lazy="noload"
    )
    predictions = relationship(
        "Prediction", back_populates="equipment", lazy="noload"
    )
    alerts = relationship("Alert", back_populates="equipment", lazy="noload")
    maintenance_logs = relationship(
        "MaintenanceLog", back_populates="equipment", lazy="noload"
    )
