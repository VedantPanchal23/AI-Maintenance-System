"""
Auto-Prediction Pipeline

Called by the simulation engine on every cycle to:
1. Store sensor readings in the database
2. Run ML inference on each reading
3. Update equipment risk_score and status
4. Generate alerts for high-risk predictions
5. Broadcast prediction results via WebSocket
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.db.models.equipment import Equipment, EquipmentStatus
from app.db.models.prediction import Prediction, FailureType, MLModel
from app.db.models.sensor import SensorReading

logger = logging.getLogger(__name__)
settings = get_settings()

# Map risk level strings → EquipmentStatus
_RISK_TO_STATUS = {
    "low": EquipmentStatus.OPERATIONAL,
    "medium": EquipmentStatus.WARNING,
    "high": EquipmentStatus.CRITICAL,
    "critical": EquipmentStatus.CRITICAL,
}

# Map probability → AlertSeverity
def _determine_severity(prob: float) -> AlertSeverity:
    if prob >= settings.ALERT_HIGH_RISK_THRESHOLD:
        return AlertSeverity.CRITICAL
    elif prob >= settings.ML_PREDICTION_THRESHOLD:
        return AlertSeverity.HIGH
    elif prob >= settings.ALERT_MEDIUM_RISK_THRESHOLD:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


async def run_auto_prediction_cycle(
    readings: List[Dict[str, Any]],
    model_service,
    session_factory,
) -> List[Dict[str, Any]]:
    """
    Full auto-prediction cycle for a batch of simulated sensor readings.

    Returns a list of prediction result dicts for WebSocket broadcast.
    """
    if not model_service or not model_service.is_loaded:
        logger.debug("No ML model loaded — skipping auto-prediction")
        return []

    prediction_results = []

    async with session_factory() as session:
        try:
            # Get the active ML model ID for linking predictions
            model_id = model_service.model_info.get("db_id")

            for reading in readings:
                equipment_id = reading.get("equipment_id")
                if not equipment_id:
                    continue

                eq_uuid = uuid.UUID(equipment_id)

                # Look up the equipment to get org_id
                eq_result = await session.execute(
                    select(Equipment).where(Equipment.id == eq_uuid)
                )
                equipment = eq_result.scalar_one_or_none()
                if not equipment:
                    continue

                org_id = equipment.organization_id

                # ── 1. Store sensor reading in DB ──
                ts = datetime.now(timezone.utc)
                sensor_record = SensorReading(
                    equipment_id=eq_uuid,
                    organization_id=org_id,
                    timestamp=ts,
                    air_temperature=reading.get("air_temperature"),
                    process_temperature=reading.get("process_temperature"),
                    rotational_speed=int(reading["rotational_speed"]) if reading.get("rotational_speed") is not None else None,
                    torque=reading.get("torque"),
                    tool_wear=int(reading["tool_wear"]) if reading.get("tool_wear") is not None else None,
                    vibration=reading.get("vibration"),
                    power_consumption=reading.get("power_consumption"),
                    pressure=reading.get("pressure"),
                    humidity=reading.get("humidity"),
                    quality_flag="good",
                )
                session.add(sensor_record)

                # ── 2. Run ML prediction ──
                sensor_data = {
                    "air_temperature": reading.get("air_temperature", 300),
                    "process_temperature": reading.get("process_temperature", 310),
                    "rotational_speed": reading.get("rotational_speed", 1500),
                    "torque": reading.get("torque", 40),
                    "tool_wear": reading.get("tool_wear", 0),
                    "vibration": reading.get("vibration", 5.0),
                }
                try:
                    result = model_service.predict(sensor_data)
                except Exception as e:
                    logger.error("Prediction failed for %s: %s", equipment_id, e, exc_info=True)
                    continue

                failure_prob = result["failure_probability"]
                risk_level = result["risk_level"]
                failure_type_str = result.get("failure_type", "none")

                # Map failure_type string to enum
                try:
                    failure_type_enum = FailureType(failure_type_str)
                except ValueError:
                    failure_type_enum = FailureType.NONE

                # ── 3. Store prediction in DB ──
                prediction = Prediction(
                    equipment_id=eq_uuid,
                    organization_id=org_id,
                    model_id=model_id,
                    timestamp=ts,
                    failure_probability=failure_prob,
                    predicted_failure=result["predicted_failure"],
                    failure_type=failure_type_enum,
                    confidence=result.get("confidence"),
                    feature_values=sensor_data,
                )
                session.add(prediction)

                # ── 4. Update equipment risk_score and status ──
                new_status = _RISK_TO_STATUS.get(risk_level, EquipmentStatus.OPERATIONAL)
                await session.execute(
                    update(Equipment)
                    .where(Equipment.id == eq_uuid)
                    .values(
                        risk_score=failure_prob,
                        status=new_status,
                    )
                )

                # ── 5. Generate alert if risk is medium or above ──
                if failure_prob >= settings.ALERT_MEDIUM_RISK_THRESHOLD:
                    severity = _determine_severity(failure_prob)

                    # De-duplicate: skip if same-severity active alert exists
                    from sqlalchemy import func
                    existing = await session.execute(
                        select(func.count(Alert.id)).where(
                            Alert.organization_id == org_id,
                            Alert.equipment_id == eq_uuid,
                            Alert.severity == severity,
                            Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
                        )
                    )
                    if existing.scalar_one() == 0:
                        alert = Alert(
                            organization_id=org_id,
                            equipment_id=eq_uuid,
                            prediction_id=prediction.id,
                            title=f"{risk_level.upper()} risk: {equipment.name}",
                            message=(
                                f"Failure probability {failure_prob:.1%} detected. "
                                f"Type: {failure_type_str.replace('_', ' ').title()}. "
                                f"Immediate attention recommended."
                            ),
                            severity=severity,
                            status=AlertStatus.ACTIVE,
                        )
                        session.add(alert)
                        logger.info(
                            "Alert generated: %s (prob=%.2f, severity=%s)",
                            equipment.name, failure_prob, severity.value,
                        )

                # ── 6. Prepare result for WebSocket broadcast ──
                prediction_results.append({
                    "equipment_id": equipment_id,
                    "equipment_name": equipment.name,
                    "failure_probability": failure_prob,
                    "predicted_failure": result["predicted_failure"],
                    "risk_level": risk_level,
                    "failure_type": failure_type_str,
                    "confidence": result.get("confidence"),
                    "timestamp": ts.isoformat(),
                })

            await session.commit()

        except Exception as e:
            logger.error("Auto-prediction cycle error: %s", e, exc_info=True)
            await session.rollback()

    return prediction_results
