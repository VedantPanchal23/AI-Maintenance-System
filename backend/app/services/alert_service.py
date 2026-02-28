"""
Alert Service

Generates, manages, and dispatches alerts based on
prediction results and threshold configurations.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.db.models.equipment import Equipment

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertService:
    """
    Business logic for alert creation and management.

    Determines severity based on configurable risk thresholds
    from settings (ALERT_HIGH_RISK_THRESHOLD, ML_PREDICTION_THRESHOLD,
    ALERT_MEDIUM_RISK_THRESHOLD).
    """

    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.organization_id = organization_id

    async def create_alert_from_prediction(
        self,
        equipment: Equipment,
        prediction_result: Dict[str, Any],
        prediction_id: Optional[uuid.UUID] = None,
    ) -> Optional[Alert]:
        """
        Create an alert based on ML prediction output.

        Only creates alert if failure_probability >= medium threshold.
        """
        prob = prediction_result["failure_probability"]

        if prob < settings.ALERT_MEDIUM_RISK_THRESHOLD:
            return None

        severity = self._determine_severity(prob)

        # ── De-duplication: skip if an ACTIVE/ACKNOWLEDGED alert of the
        #    same severity already exists for this equipment. ──
        existing = await self.db.execute(
            select(func.count(Alert.id)).where(
                Alert.organization_id == self.organization_id,
                Alert.equipment_id == equipment.id,
                Alert.severity == severity,
                Alert.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]),
            )
        )
        if existing.scalar_one() > 0:
            logger.debug(
                "Duplicate alert suppressed for %s (severity=%s)",
                equipment.name, severity.value,
            )
            return None

        failure_type = prediction_result.get("failure_type", "unknown")

        title = f"{severity.value.upper()} Risk: {equipment.name}"
        message = (
            f"Equipment '{equipment.name}' ({equipment.equipment_type.value}) "
            f"has a {prob:.1%} probability of failure. "
            f"Predicted failure mode: {failure_type}. "
            f"Immediate inspection recommended."
        )

        if severity in (AlertSeverity.CRITICAL, AlertSeverity.HIGH):
            message += (
                " This equipment should be taken offline for preventive "
                "maintenance to avoid unplanned downtime."
            )

        alert = Alert(
            organization_id=self.organization_id,
            equipment_id=equipment.id,
            prediction_id=prediction_id,
            severity=severity,
            status=AlertStatus.ACTIVE,
            title=title,
            message=message,
            risk_score=prob,
        )
        self.db.add(alert)
        await self.db.flush()

        logger.info(
            "Alert created: %s [severity=%s, risk=%.2f] for %s",
            alert.id, severity.value, prob, equipment.name,
        )

        # Email notification (if enabled)
        if settings.ALERT_EMAIL_ENABLED and severity in (
            AlertSeverity.CRITICAL, AlertSeverity.HIGH
        ):
            await self._send_email_notification(alert, equipment)

        return alert

    def _determine_severity(self, failure_probability: float) -> AlertSeverity:
        """Map failure probability to alert severity."""
        if failure_probability >= settings.ALERT_HIGH_RISK_THRESHOLD:
            return AlertSeverity.CRITICAL
        elif failure_probability >= settings.ML_PREDICTION_THRESHOLD:
            return AlertSeverity.HIGH
        elif failure_probability >= settings.ALERT_MEDIUM_RISK_THRESHOLD:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW

    async def _send_email_notification(
        self, alert: Alert, equipment: Equipment
    ) -> None:
        """Send email notification for high-severity alerts."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText

            msg = MIMEText(
                f"ALERT: {alert.title}\n\n"
                f"{alert.message}\n\n"
                f"Equipment: {equipment.name}\n"
                f"Location: {equipment.location or 'N/A'}\n"
                f"Risk Score: {alert.risk_score:.2%}\n"
                f"Time: {datetime.now(timezone.utc).isoformat()}\n\n"
                f"Please log in to the dashboard for details."
            )
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg["From"] = settings.ALERT_FROM_EMAIL
            msg["To"] = settings.SMTP_USER  # Send to admin; extend for team

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )

            alert.email_sent = True
            logger.info("Alert email sent for alert %s", alert.id)

        except Exception as e:
            logger.error("Failed to send alert email: %s", str(e))
