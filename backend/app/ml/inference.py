"""
ML Model Inference Service

Loads trained models and serves predictions with sub-100ms latency.
Supports model hot-swapping, GPU inference, and fallback strategies.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from app.config import get_settings
from app.core.risk import compute_risk_level as _compute_risk_level
from app.ml.features import FeatureEngineer

logger = logging.getLogger(__name__)
settings = get_settings()

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class ModelInferenceService:
    """
    Production inference service.

    - Loads model artifacts (model + scaler + feature list)
    - Serves predictions via predict() method
    - Supports model versioning and hot reload
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir or settings.ML_MODEL_DIR)
        self._active_model = None
        self._active_model_info: Dict[str, Any] = {}
        self._feature_engineer = FeatureEngineer()

    @property
    def is_loaded(self) -> bool:
        return self._active_model is not None

    @property
    def model_info(self) -> Dict[str, Any]:
        return self._active_model_info

    async def load_default_model(self) -> None:
        """Load the most recent model matching the default algorithm."""
        await self.load_latest_model(settings.ML_DEFAULT_MODEL)

    async def load_latest_model(self, algorithm: Optional[str] = None) -> None:
        """Find and load the most recently saved model file."""
        pattern = f"{algorithm}_*.joblib" if algorithm else "*.joblib"
        model_files = sorted(self.model_dir.glob(pattern), reverse=True)

        if not model_files:
            raise FileNotFoundError(
                f"No model files found in {self.model_dir} "
                f"matching '{pattern}'"
            )

        await self.load_model(str(model_files[0]))

    async def load_model(self, model_path: str) -> None:
        """Load a specific model artifact."""
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        artifact = joblib.load(path)

        self._active_model = artifact["model"]
        self._feature_engineer.scaler = artifact["scaler"]
        self._feature_engineer._is_fitted = True
        self._active_model_info = {
            "algorithm": artifact["algorithm"],
            "version": artifact["version"],
            "model_path": str(path),
            "feature_columns": artifact["feature_columns"],
            "metrics": artifact.get("metrics", {}),
        }

        # Ensure PyTorch model is on correct device and in eval mode
        if TORCH_AVAILABLE and hasattr(self._active_model, "model"):
            try:
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self._active_model.device = device
                self._active_model.model.to(device)
                self._active_model.model.eval()
                self._active_model_info["device"] = str(device)
                logger.info("PyTorch model moved to %s for inference", device)
            except Exception as e:
                logger.warning("Could not move model to GPU: %s", e)

        logger.info(
            "Loaded model: %s v%s (F1=%.4f)",
            artifact["algorithm"],
            artifact["version"],
            artifact.get("metrics", {}).get("f1", 0),
        )

    def predict(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run prediction on a single sensor reading.

        Args:
            sensor_data: dict with keys matching FEATURE_COLUMNS
                e.g. {"air_temperature": 300.1, "rotational_speed": 1500, ...}

        Returns:
            {
                "failure_probability": 0.85,
                "predicted_failure": True,
                "confidence": 0.85,
                "failure_type": "tool_wear",
                "risk_level": "high",
                "feature_importance": {...}
            }
        """
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")

        df = pd.DataFrame([sensor_data])
        X = self._feature_engineer.prepare_for_inference(df)

        # Get probability prediction
        if hasattr(self._active_model, "predict_proba"):
            proba = self._active_model.predict_proba(X)[0]
            failure_prob = float(proba[1])
        else:
            pred = self._active_model.predict(X)[0]
            failure_prob = float(pred)

        predicted_failure = failure_prob >= settings.ML_PREDICTION_THRESHOLD

        # Determine risk level
        risk_level = _compute_risk_level(failure_prob)

        # Determine likely failure type based on feature values
        failure_type = self._infer_failure_type(sensor_data, failure_prob)

        # Feature importance (if tree-based model)
        feature_importance = self._get_feature_importance(sensor_data)

        return {
            "failure_probability": round(failure_prob, 4),
            "predicted_failure": predicted_failure,
            "confidence": round(max(failure_prob, 1 - failure_prob), 4),
            "failure_type": failure_type,
            "risk_level": risk_level,
            "model_version": self._active_model_info.get("version", "unknown"),
            "feature_importance": feature_importance,
        }

    def predict_batch(self, sensor_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run predictions on multiple sensor readings using vectorized inference."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
        if not sensor_data_list:
            return []

        # Batch prepare all data into one DataFrame
        df = pd.DataFrame(sensor_data_list)
        X = self._feature_engineer.prepare_for_inference(df)

        # Batch probability prediction
        if hasattr(self._active_model, "predict_proba"):
            probas = self._active_model.predict_proba(X)[:, 1]
        else:
            probas = self._active_model.predict(X).astype(float)

        results = []
        for i, (sensor_data, failure_prob) in enumerate(zip(sensor_data_list, probas)):
            failure_prob = float(failure_prob)
            predicted_failure = failure_prob >= settings.ML_PREDICTION_THRESHOLD
            risk_level = _compute_risk_level(failure_prob)
            failure_type = self._infer_failure_type(sensor_data, failure_prob)

            results.append({
                "failure_probability": round(failure_prob, 4),
                "predicted_failure": predicted_failure,
                "confidence": round(max(failure_prob, 1 - failure_prob), 4),
                "failure_type": failure_type,
                "risk_level": risk_level,
                "model_version": self._active_model_info.get("version", "unknown"),
            })

        return results

    def _infer_failure_type(self, data: Dict[str, Any], prob: float) -> str:
        """Heuristic failure type classification based on sensor patterns."""
        if prob < settings.ML_PREDICTION_THRESHOLD:
            return "none"

        tool_wear = data.get("tool_wear", 0)
        torque = data.get("torque", 0)
        speed = data.get("rotational_speed", 0)
        temp_diff = data.get("process_temperature", 0) - data.get("air_temperature", 0)
        power = torque * speed * 2 * 3.14159 / 60

        # Priority-based failure mode detection
        if tool_wear > 200 and torque > 50:
            return "overstrain"
        if tool_wear > 200:
            return "tool_wear"
        if temp_diff < 8.6 and speed < 1380:
            return "heat_dissipation"
        if power < 3500 or power > 9000:
            return "power_failure"

        return "random"

    def _get_feature_importance(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract top feature importances from tree-based models or PyTorch gradient-based."""
        feature_cols = self._active_model_info.get("feature_columns", [])

        # Tree-based models have feature_importances_ directly
        if hasattr(self._active_model, "feature_importances_"):
            importances = self._active_model.feature_importances_
            if len(importances) != len(feature_cols):
                return {}
            paired = sorted(
                zip(feature_cols, importances), key=lambda x: x[1], reverse=True
            )[:10]
            return {name: round(float(imp), 4) for name, imp in paired}

        # For PyTorch NN — return top features by absolute input magnitude × weight
        if TORCH_AVAILABLE and hasattr(self._active_model, "model"):
            try:
                first_layer = list(self._active_model.model.network.children())[0]
                if hasattr(first_layer, "weight"):
                    weights = first_layer.weight.data.abs().mean(dim=0).cpu().numpy()
                    if len(weights) == len(feature_cols):
                        paired = sorted(
                            zip(feature_cols, weights),
                            key=lambda x: x[1], reverse=True
                        )[:10]
                        return {name: round(float(w), 4) for name, w in paired}
            except Exception:
                pass

        return {}
