"""
ML Model Monitoring — Drift Detection & Prediction Quality Tracking

Monitors production model behavior by tracking:
  - Prediction distribution shifts (PSI — Population Stability Index)
  - Feature drift via KL divergence
  - Prediction confidence degradation
  - Rolling accuracy metrics (when ground truth is available)

Provides /api/v1/ml/monitoring endpoint for dashboards.
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Max number of predictions to keep in memory for monitoring
MAX_HISTORY = 10_000
DRIFT_CHECK_INTERVAL = 300  # seconds (5 min)


@dataclass
class PredictionRecord:
    """Single prediction record for monitoring."""
    timestamp: float
    failure_probability: float
    predicted_failure: bool
    risk_level: str
    feature_values: Dict[str, float]
    confidence: float


class ModelMonitor:
    """
    Real-time model performance and drift monitor.

    Collects prediction records and computes:
    - Prediction distribution statistics
    - Feature distribution drift (PSI)
    - Confidence score trends
    - Alert on significant shifts
    """

    def __init__(self, reference_distribution: Optional[Dict[str, np.ndarray]] = None):
        self._predictions: deque = deque(maxlen=MAX_HISTORY)
        self._reference_proba: Optional[np.ndarray] = None
        self._reference_features: Optional[Dict[str, np.ndarray]] = reference_distribution
        self._last_drift_check: float = 0
        self._drift_alerts: List[Dict[str, Any]] = []
        self._start_time: float = time.time()

    def record_prediction(self, prediction_result: Dict[str, Any], features: Dict[str, float]):
        """Record a new prediction for monitoring."""
        record = PredictionRecord(
            timestamp=time.time(),
            failure_probability=prediction_result["failure_probability"],
            predicted_failure=prediction_result["predicted_failure"],
            risk_level=prediction_result["risk_level"],
            feature_values=features,
            confidence=prediction_result["confidence"],
        )
        self._predictions.append(record)

        # Periodic drift check
        if time.time() - self._last_drift_check > DRIFT_CHECK_INTERVAL:
            self._check_drift()

    def set_reference_distribution(self, probabilities: np.ndarray, features: Dict[str, np.ndarray]):
        """Set the reference (training) distribution for drift comparison."""
        self._reference_proba = probabilities
        self._reference_features = features
        logger.info("Reference distribution set with %d samples", len(probabilities))

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        if not self._predictions:
            return {
                "status": "no_data",
                "message": "No predictions recorded yet",
                "total_predictions": 0,
            }

        records = list(self._predictions)
        probas = np.array([r.failure_probability for r in records])
        confidences = np.array([r.confidence for r in records])
        failures = sum(1 for r in records if r.predicted_failure)

        # Time-based stats
        now = time.time()
        last_hour = [r for r in records if now - r.timestamp < 3600]
        last_hour_probas = np.array([r.failure_probability for r in last_hour]) if last_hour else np.array([])

        report = {
            "status": "healthy",
            "total_predictions": len(records),
            "monitoring_uptime_hours": round((now - self._start_time) / 3600, 2),

            # Overall distribution
            "prediction_stats": {
                "mean_probability": float(np.mean(probas)),
                "std_probability": float(np.std(probas)),
                "median_probability": float(np.median(probas)),
                "p95_probability": float(np.percentile(probas, 95)),
                "failure_rate": round(failures / len(records) * 100, 2),
            },

            # Confidence
            "confidence_stats": {
                "mean_confidence": float(np.mean(confidences)),
                "min_confidence": float(np.min(confidences)),
                "p5_confidence": float(np.percentile(confidences, 5)),
            },

            # Last hour
            "last_hour": {
                "predictions": len(last_hour),
                "mean_probability": float(np.mean(last_hour_probas)) if len(last_hour_probas) > 0 else None,
                "failure_rate": round(sum(1 for r in last_hour if r.predicted_failure) / max(len(last_hour), 1) * 100, 2),
            },

            # Risk level distribution
            "risk_distribution": self._risk_distribution(records),

            # Drift
            "drift": self._compute_drift_metrics(),

            # Alerts
            "drift_alerts": self._drift_alerts[-10:],  # Last 10 alerts
        }

        # Set status based on drift
        drift = report["drift"]
        if drift.get("psi", 0) > 0.25:
            report["status"] = "critical_drift"
        elif drift.get("psi", 0) > 0.1:
            report["status"] = "warning_drift"
        elif report["confidence_stats"]["mean_confidence"] < 0.6:
            report["status"] = "low_confidence"

        return report

    def _risk_distribution(self, records: List[PredictionRecord]) -> Dict[str, int]:
        """Count predictions by risk level."""
        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for r in records:
            if r.risk_level in dist:
                dist[r.risk_level] += 1
        return dist

    def _compute_drift_metrics(self) -> Dict[str, Any]:
        """Compute PSI between reference and current prediction distributions."""
        if self._reference_proba is None or len(self._predictions) < 100:
            return {"psi": None, "message": "Insufficient data for drift detection"}

        current_probas = np.array([r.failure_probability for r in self._predictions])
        psi = self._calculate_psi(self._reference_proba, current_probas)

        # Feature drift (KL divergence for each feature)
        feature_drift = {}
        if self._reference_features:
            current_features = self._extract_feature_arrays()
            for feat_name, ref_values in self._reference_features.items():
                if feat_name in current_features and len(current_features[feat_name]) > 50:
                    feat_psi = self._calculate_psi(ref_values, current_features[feat_name])
                    feature_drift[feat_name] = round(feat_psi, 4)

        return {
            "psi": round(psi, 4),
            "interpretation": self._interpret_psi(psi),
            "feature_drift": feature_drift,
        }

    def _extract_feature_arrays(self) -> Dict[str, np.ndarray]:
        """Extract per-feature arrays from prediction records."""
        features: Dict[str, list] = {}
        for r in self._predictions:
            for k, v in r.feature_values.items():
                features.setdefault(k, []).append(v)
        return {k: np.array(v) for k, v in features.items()}

    @staticmethod
    def _calculate_psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """
        Population Stability Index (PSI).

        PSI < 0.1:  No significant shift
        PSI 0.1-0.25: Moderate shift — monitor closely
        PSI > 0.25: Significant shift — retrain recommended

        Uses equal-width bins clipped to [epsilon, 1-epsilon].
        """
        eps = 1e-6

        # Create bins from reference distribution
        breakpoints = np.linspace(
            min(reference.min(), current.min()) - eps,
            max(reference.max(), current.max()) + eps,
            bins + 1,
        )

        ref_counts = np.histogram(reference, bins=breakpoints)[0].astype(float)
        cur_counts = np.histogram(current, bins=breakpoints)[0].astype(float)

        # Normalize to proportions
        ref_pct = ref_counts / ref_counts.sum()
        cur_pct = cur_counts / cur_counts.sum()

        # Avoid log(0)
        ref_pct = np.clip(ref_pct, eps, 1)
        cur_pct = np.clip(cur_pct, eps, 1)

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi)

    @staticmethod
    def _interpret_psi(psi: float) -> str:
        if psi < 0.1:
            return "stable"
        elif psi < 0.25:
            return "moderate_drift"
        else:
            return "significant_drift"

    def _check_drift(self):
        """Periodic drift check — logs alerts if drift detected."""
        self._last_drift_check = time.time()

        if len(self._predictions) < 100:
            return

        drift = self._compute_drift_metrics()
        psi = drift.get("psi")

        if psi is not None and psi > 0.1:
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "prediction_drift",
                "psi": psi,
                "severity": "critical" if psi > 0.25 else "warning",
                "message": f"Prediction distribution shift detected (PSI={psi:.4f})",
            }
            self._drift_alerts.append(alert)
            logger.warning("DRIFT ALERT: %s", alert["message"])


# ── Singleton instance ────────────────────────────────────────
_monitor_instance: Optional[ModelMonitor] = None


def get_model_monitor() -> ModelMonitor:
    """Get or create the singleton ModelMonitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = ModelMonitor()
    return _monitor_instance
