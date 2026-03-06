"""
Shared risk level computation — single source of truth.

Used by predictions endpoint, inference service, and alert service.
"""

from app.config import get_settings


def compute_risk_level(failure_probability: float) -> str:
    """Canonical risk-level classification based on failure probability."""
    settings = get_settings()
    if failure_probability >= settings.ALERT_HIGH_RISK_THRESHOLD:
        return "critical"
    elif failure_probability >= settings.ML_PREDICTION_THRESHOLD:
        return "high"
    elif failure_probability >= settings.ALERT_MEDIUM_RISK_THRESHOLD:
        return "medium"
    return "low"
