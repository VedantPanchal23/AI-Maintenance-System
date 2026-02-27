"""
Feature Engineering Pipeline

Transforms raw sensor readings into ML-ready features.
Includes rolling statistics, lag features, rate-of-change,
and domain-specific engineered features.
"""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Feature Definitions
# ═══════════════════════════════════════════════════════════════

BASE_FEATURES = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "vibration",
]

ENGINEERED_FEATURES = [
    # Derived physical quantities
    "temp_difference",
    "power",
    "torque_speed_ratio",
    "mechanical_stress",

    # Rolling statistics (window=5)
    "vibration_rolling_mean_5",
    "vibration_rolling_std_5",
    "torque_rolling_mean_5",
    "temp_diff_rolling_mean_5",
    "speed_rolling_std_5",

    # Rate of change
    "vibration_rate_of_change",
    "torque_rate_of_change",
    "temp_rate_of_change",

    # Interaction features
    "wear_torque_interaction",
    "speed_torque_product",
    "temp_vibration_interaction",

    # Threshold indicators
    "high_vibration_flag",
    "high_torque_flag",
    "high_temp_flag",
    "high_wear_flag",
]


# ═══════════════════════════════════════════════════════════════
# Feature Engineering
# ═══════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Transforms raw sensor data into ML-ready feature vectors."""

    def __init__(self, scaler: Optional[StandardScaler] = None):
        self.scaler = scaler or StandardScaler()
        self._is_fitted = False

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all feature engineering transformations.

        For batch training: pass full DataFrame.
        For real-time inference: pass single row or small batch.
        """
        df = df.copy()

        # ── Derived Physical Features ──
        df["temp_difference"] = df["process_temperature"] - df["air_temperature"]

        df["power"] = (
            df["torque"] * df["rotational_speed"] * 2 * np.pi / 60
        )  # Watts

        df["torque_speed_ratio"] = np.where(
            df["rotational_speed"] > 0,
            df["torque"] / df["rotational_speed"],
            0,
        )

        df["mechanical_stress"] = (
            df["torque"] * df["tool_wear"] / 1000.0
        )  # Combined stress indicator

        # ── Rolling Statistics (only meaningful for time-ordered data) ──
        if len(df) >= 5:
            df["vibration_rolling_mean_5"] = (
                df["vibration"].rolling(window=5, min_periods=1).mean()
            )
            df["vibration_rolling_std_5"] = (
                df["vibration"].rolling(window=5, min_periods=1).std().fillna(0)
            )
            df["torque_rolling_mean_5"] = (
                df["torque"].rolling(window=5, min_periods=1).mean()
            )
            df["temp_diff_rolling_mean_5"] = (
                df["temp_difference"].rolling(window=5, min_periods=1).mean()
            )
            df["speed_rolling_std_5"] = (
                df["rotational_speed"].rolling(window=5, min_periods=1).std().fillna(0)
            )
        else:
            # Single-row inference: use raw values as rolling proxies
            df["vibration_rolling_mean_5"] = df["vibration"]
            df["vibration_rolling_std_5"] = 0.0
            df["torque_rolling_mean_5"] = df["torque"]
            df["temp_diff_rolling_mean_5"] = df["temp_difference"]
            df["speed_rolling_std_5"] = 0.0

        # ── Rate of Change ──
        if len(df) > 1:
            df["vibration_rate_of_change"] = df["vibration"].diff().fillna(0)
            df["torque_rate_of_change"] = df["torque"].diff().fillna(0)
            df["temp_rate_of_change"] = df["temp_difference"].diff().fillna(0)
        else:
            df["vibration_rate_of_change"] = 0.0
            df["torque_rate_of_change"] = 0.0
            df["temp_rate_of_change"] = 0.0

        # ── Interaction Features ──
        df["wear_torque_interaction"] = df["tool_wear"] * df["torque"]
        df["speed_torque_product"] = df["rotational_speed"] * df["torque"]
        df["temp_vibration_interaction"] = df["temp_difference"] * df["vibration"]

        # ── Threshold Indicators ──
        df["high_vibration_flag"] = (df["vibration"] > 8.0).astype(int)
        df["high_torque_flag"] = (df["torque"] > 55.0).astype(int)
        df["high_temp_flag"] = (df["temp_difference"] > 12.0).astype(int)
        df["high_wear_flag"] = (df["tool_wear"] > 200).astype(int)

        return df

    def get_feature_columns(self) -> List[str]:
        """Return the ordered list of all feature columns used in training."""
        return BASE_FEATURES + ENGINEERED_FEATURES

    def prepare_for_training(
        self, df: pd.DataFrame, target_col: str = "failure"
    ) -> tuple:
        """
        Full feature engineering + scaling for model training.

        Returns: (X_scaled, y, feature_names)
        """
        df = self.engineer_features(df)
        feature_cols = self.get_feature_columns()

        # Ensure all columns exist
        missing = [c for c in feature_cols if c not in df.columns]
        if missing:
            logger.warning("Missing features (will zero-fill): %s", missing)
            for col in missing:
                df[col] = 0.0

        X = df[feature_cols].values.astype(np.float32)
        y = df[target_col].values.astype(np.int32)

        # Replace NaN/Inf
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        # Fit scaler on training data
        X_scaled = self.scaler.fit_transform(X)
        self._is_fitted = True

        logger.info(
            "Prepared %d samples with %d features for training",
            X_scaled.shape[0],
            X_scaled.shape[1],
        )
        return X_scaled, y, feature_cols

    def prepare_for_inference(self, df: pd.DataFrame) -> np.ndarray:
        """
        Feature engineering + scaling for inference (scaler must be fitted).
        """
        if not self._is_fitted:
            raise RuntimeError("Scaler not fitted. Call prepare_for_training first.")

        df = self.engineer_features(df)
        feature_cols = self.get_feature_columns()

        missing = [c for c in feature_cols if c not in df.columns]
        for col in missing:
            df[col] = 0.0

        X = df[feature_cols].values.astype(np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        return self.scaler.transform(X)
