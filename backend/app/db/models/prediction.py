"""
Prediction & ML Model Registry

Stores prediction results and model metadata/versions.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class FailureType(str, PyEnum):
    NONE = "none"
    HEAT_DISSIPATION = "heat_dissipation"
    POWER_FAILURE = "power_failure"
    OVERSTRAIN = "overstrain"
    TOOL_WEAR = "tool_wear"
    RANDOM = "random"


class Prediction(Base, TenantMixin):
    """ML prediction result for a specific equipment reading."""

    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("equipment.id"), nullable=False, index=True
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Prediction output
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_failure: Mapped[bool] = mapped_column(nullable=False)
    failure_type: Mapped[FailureType] = mapped_column(
        Enum(FailureType), default=FailureType.NONE
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    # Feature snapshot (for explainability)
    feature_values: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationships
    equipment = relationship("Equipment", back_populates="predictions")
    model = relationship("MLModel", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_equip_time", "equipment_id", "timestamp"),
    )


class MLModel(Base, TimestampMixin):
    """Registry for trained ML models — supports versioning."""

    __tablename__ = "ml_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)  # rf, xgboost, lgbm, nn
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # File path to saved model artifact
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    is_default: Mapped[bool] = mapped_column(default=False)

    # Performance metrics
    accuracy: Mapped[float] = mapped_column(Float, nullable=True)
    precision: Mapped[float] = mapped_column(Float, nullable=True)
    recall: Mapped[float] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float] = mapped_column(Float, nullable=True)
    auc_roc: Mapped[float] = mapped_column(Float, nullable=True)

    # Training metadata
    training_samples: Mapped[int] = mapped_column(Integer, nullable=True)
    feature_columns: Mapped[dict] = mapped_column(JSON, nullable=True)
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    training_duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    # Relationships
    predictions = relationship("Prediction", back_populates="model", lazy="noload")
    training_runs = relationship("MLTrainingRun", back_populates="model", lazy="noload")


class MLTrainingRun(Base, TimestampMixin):
    """Tracks individual training experiments."""

    __tablename__ = "ml_training_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_models.id"), nullable=True
    )
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | completed | failed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metrics logged during training
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    dataset_info: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Relationships
    model = relationship("MLModel", back_populates="training_runs")
