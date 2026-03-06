"""
Organization & User Models

Multi-tenant SaaS entities with RBAC.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, PyEnum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class Organization(Base, TimestampMixin):
    """Tenant entity — represents a factory / organization."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_equipment: Mapped[int] = mapped_column(default=50)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="standard")

    # Relationships
    users = relationship("User", back_populates="organization", lazy="noload")
    equipment = relationship("Equipment", back_populates="organization", lazy="noload")


class User(Base, TimestampMixin):
    """User entity with role-based access."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.ENGINEER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Alert / notification preferences
    notification_email: Mapped[str] = mapped_column(String(255), nullable=True)
    alert_preferences: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        default=lambda: {"email_enabled": True, "severities": ["critical", "high"]},
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
