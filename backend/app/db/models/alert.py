"""
Alert & Maintenance Log Models

Alert system for threshold-based and ML-based notifications.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class AlertSeverity(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, PyEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Alert(Base, TimestampMixin, TenantMixin):
    """Alert generated when equipment risk exceeds threshold."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False, index=True
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=True
    )

    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity), nullable=False, index=True
    )
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus), default=AlertStatus.ACTIVE, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)

    # Resolution tracking
    acknowledged_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Email notification tracking
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    equipment = relationship("Equipment", back_populates="alerts")
    prediction = relationship("Prediction", lazy="noload")


class MaintenanceLog(Base, TimestampMixin, TenantMixin):
    """Record of maintenance activities performed on equipment."""

    __tablename__ = "maintenance_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False, index=True
    )
    performed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    maintenance_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # preventive | corrective | predictive
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Kanban Board Tracking
    status: Mapped[str] = mapped_column(String(20), default="todo", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cost: Mapped[float] = mapped_column(Float, nullable=True)
    downtime_hours: Mapped[float] = mapped_column(Float, nullable=True)
    parts_replaced: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    equipment = relationship("Equipment", back_populates="maintenance_logs")
    performer = relationship("User", lazy="noload")


class AuditLog(Base, TimestampMixin, TenantMixin):
    """Audit trail for admin / security-relevant actions."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    # Relationships
    user = relationship("User", lazy="noload")
