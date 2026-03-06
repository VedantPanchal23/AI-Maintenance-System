"""
Prediction Endpoints

POST /predictions/predict          — Run real-time prediction
GET  /predictions/history/{equip}  — Prediction history for equipment
GET  /predictions/latest/{equip}   — Latest prediction for equipment
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.api.v1.deps import get_current_user, get_db
from app.api.v1.schemas import PredictionRequest, PredictionResponse, PredictionHistoryResponse

settings = get_settings()
from app.core.exceptions import MLModelException, NotFoundException
from app.core.risk import compute_risk_level as _compute_risk_level
from app.db.models.equipment import Equipment, EquipmentStatus
from app.db.models.prediction import Prediction, FailureType

from app.db.models.organization import User
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
@limiter.limit("60/minute")
async def predict_failure(
    request: Request,
    body: PredictionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run equipment failure prediction.

    Accepts sensor readings and returns failure probability,
    risk level, and failure type classification.
    """
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

    # Get model service from app state
    model_service = request.app.state.model_service
    if not model_service.is_loaded:
        raise MLModelException("ML model is not loaded. Please train a model first.")

    # Prepare sensor data for prediction
    sensor_data = {
        "air_temperature": body.air_temperature,
        "process_temperature": body.process_temperature,
        "rotational_speed": body.rotational_speed,
        "torque": body.torque,
        "tool_wear": body.tool_wear,
        "vibration": body.vibration,
    }

    # Run inference (offload to thread to avoid blocking event loop)
    prediction_result = await asyncio.to_thread(model_service.predict, sensor_data)

    now = datetime.now(timezone.utc)

    # Store prediction in database
    prediction = Prediction(
        organization_id=user.organization_id,
        equipment_id=body.equipment_id,
        timestamp=now,
        failure_probability=prediction_result["failure_probability"],
        predicted_failure=prediction_result["predicted_failure"],
        failure_type=FailureType(prediction_result["failure_type"]),
        confidence=prediction_result["confidence"],
        feature_values=sensor_data,
    )
    db.add(prediction)

    # Update equipment risk score
    equipment.risk_score = prediction_result["failure_probability"]
    if prediction_result["risk_level"] == "critical":
        equipment.status = EquipmentStatus.CRITICAL
    elif prediction_result["risk_level"] == "high":
        equipment.status = EquipmentStatus.WARNING

    await db.flush()

    # Trigger alert if risk level warrants it
    if prediction_result["failure_probability"] >= 0.5:
        from app.services.alert_service import AlertService
        alert_service = AlertService(db, user.organization_id)
        await alert_service.create_alert_from_prediction(
            equipment=equipment,
            prediction_result=prediction_result,
            prediction_id=prediction.id,
        )

    logger.info(
        "Prediction for %s: prob=%.4f, risk=%s",
        equipment.name,
        prediction_result["failure_probability"],
        prediction_result["risk_level"],
    )

    # Record in model monitor for drift detection
    try:
        from app.ml.monitoring import get_model_monitor
        monitor = get_model_monitor()
        monitor.record_prediction(prediction_result, sensor_data)
    except Exception as e:
        logger.warning("Monitoring recording failed (non-critical): %s", e)

    return PredictionResponse(
        id=prediction.id,
        equipment_id=body.equipment_id,
        timestamp=now,
        failure_probability=prediction_result["failure_probability"],
        predicted_failure=prediction_result["predicted_failure"],
        failure_type=prediction_result["failure_type"],
        confidence=prediction_result["confidence"],
        risk_level=prediction_result["risk_level"],
        model_version=prediction_result["model_version"],
        feature_importance=prediction_result.get("feature_importance"),
    )


@router.get("/history/{equipment_id}", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    equipment_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get prediction history for an equipment."""
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.equipment_id == equipment_id,
            Prediction.organization_id == user.organization_id,
        )
        .order_by(Prediction.timestamp.desc())
        .limit(limit)
    )
    predictions = result.scalars().all()

    items = [
        PredictionResponse(
            id=p.id,
            equipment_id=p.equipment_id,
            timestamp=p.timestamp,
            failure_probability=p.failure_probability,
            predicted_failure=p.predicted_failure,
            failure_type=p.failure_type.value if p.failure_type else "none",
            confidence=p.confidence or 0,
            risk_level=_compute_risk_level(p.failure_probability),
            model_version="stored",
        )
        for p in predictions
    ]

    return PredictionHistoryResponse(
        items=items,
        total=len(items),
        equipment_id=equipment_id,
    )


@router.get("/latest/{equipment_id}", response_model=PredictionResponse)
async def get_latest_prediction(
    equipment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent prediction for an equipment."""
    result = await db.execute(
        select(Prediction)
        .where(
            Prediction.equipment_id == equipment_id,
            Prediction.organization_id == user.organization_id,
        )
        .order_by(Prediction.timestamp.desc())
        .limit(1)
    )
    prediction = result.scalar_one_or_none()

    if not prediction:
        raise NotFoundException("Prediction for equipment", equipment_id)

    return PredictionResponse(
        id=prediction.id,
        equipment_id=prediction.equipment_id,
        timestamp=prediction.timestamp,
        failure_probability=prediction.failure_probability,
        predicted_failure=prediction.predicted_failure,
        failure_type=prediction.failure_type.value if prediction.failure_type else "none",
        confidence=prediction.confidence or 0,
        risk_level=_compute_risk_level(prediction.failure_probability),
        model_version="stored",
    )
