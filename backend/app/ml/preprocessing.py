"""
Data Preprocessing Pipeline

Handles data loading, cleaning, validation, and preparation
for the ML feature engineering stage.

Supports:
- AI4I Predictive Maintenance Dataset
- NASA Turbofan Engine Degradation Dataset
- Custom sensor data from the platform
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

AI4I_COLUMNS = [
    "UDI", "Product ID", "Type", "Air temperature [K]",
    "Process temperature [K]", "Rotational speed [rpm]",
    "Torque [Nm]", "Tool wear [min]", "Machine failure",
    "TWF", "HDF", "PWF", "OSF", "RNF",
]

FEATURE_COLUMNS = [
    "air_temperature", "process_temperature", "rotational_speed",
    "torque", "tool_wear", "vibration",
]

TARGET_COLUMN = "failure"


# ═══════════════════════════════════════════════════════════════
# Data Loader
# ═══════════════════════════════════════════════════════════════

class DataPreprocessor:
    """Orchestrates data loading, cleaning, and validation."""

    def __init__(self, data_dir: str = "./data/raw"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_ai4i_dataset(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load and normalize the AI4I Predictive Maintenance dataset.

        If no file path is provided, generates synthetic data
        matching the AI4I distribution for development/demo.
        """
        if filepath and Path(filepath).exists():
            logger.info("Loading AI4I dataset from %s", filepath)
            df = pd.read_csv(filepath)
            return self._normalize_ai4i(df)

        logger.info("Generating synthetic AI4I-compatible dataset")
        return self._generate_synthetic_data(n_samples=10000)

    def _normalize_ai4i(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map raw AI4I columns to standardized feature names."""
        column_map = {
            "Air temperature [K]": "air_temperature",
            "Process temperature [K]": "process_temperature",
            "Rotational speed [rpm]": "rotational_speed",
            "Torque [Nm]": "torque",
            "Tool wear [min]": "tool_wear",
            "Machine failure": "failure",
            "TWF": "tool_wear_failure",
            "HDF": "heat_dissipation_failure",
            "PWF": "power_failure",
            "OSF": "overstrain_failure",
            "RNF": "random_failure",
        }
        df = df.rename(columns=column_map)

        # Add synthetic vibration (correlated with torque + speed)
        if "vibration" not in df.columns:
            np.random.seed(42)
            df["vibration"] = (
                0.3 * df["torque"] / df["torque"].max()
                + 0.3 * df["rotational_speed"] / df["rotational_speed"].max()
                + 0.4 * np.random.uniform(0, 1, len(df))
            ) * 10  # mm/s scale

        return df

    def _generate_synthetic_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """
        Generate synthetic sensor data matching AI4I statistical properties.

        Distribution parameters sourced from AI4I dataset documentation:
        - Air temp: ~300K, std=2K
        - Process temp: air_temp + 10K, std=1K
        - Rotational speed: ~1500 RPM (bimodal)
        - Torque: ~40 Nm, std=10
        - Tool wear: 0-240 min uniform
        """
        np.random.seed(42)

        # Product quality type (L=50%, M=30%, H=20%)
        types = np.random.choice(
            ["L", "M", "H"], size=n_samples, p=[0.5, 0.3, 0.2]
        )

        air_temp = np.random.normal(300.0, 2.0, n_samples)
        process_temp = air_temp + 10.0 + np.random.normal(0, 1.0, n_samples)
        rotational_speed = np.random.normal(1538.0, 177.0, n_samples).clip(1000, 2900)
        torque = np.random.normal(39.98, 9.97, n_samples).clip(5, 80)
        tool_wear = np.random.randint(0, 241, n_samples)

        # Vibration correlated with mechanical stress
        vibration = (
            0.25 * (torque / 80.0) +
            0.25 * (rotational_speed / 2900.0) +
            0.2 * (tool_wear / 240.0) +
            0.3 * np.random.uniform(0, 1, n_samples)
        ) * 12.0

        df = pd.DataFrame({
            "product_type": types,
            "air_temperature": air_temp,
            "process_temperature": process_temp,
            "rotational_speed": rotational_speed.astype(int),
            "torque": np.round(torque, 2),
            "tool_wear": tool_wear,
            "vibration": np.round(vibration, 2),
        })

        # ── Failure Logic (matching AI4I failure modes) ──
        df["failure"] = 0

        # Tool Wear Failure: tool_wear between 200-240 (random ~1/3 chance)
        twf_mask = (df["tool_wear"] >= 200) & (np.random.random(n_samples) < 0.33)
        df.loc[twf_mask, "failure"] = 1

        # Heat Dissipation Failure: temp diff < 8.6K and speed < 1380
        temp_diff = df["process_temperature"] - df["air_temperature"]
        hdf_mask = (temp_diff < 8.6) & (df["rotational_speed"] < 1380)
        df.loc[hdf_mask, "failure"] = 1

        # Power Failure: power outside [3500, 9000] W
        power = df["torque"] * df["rotational_speed"] * 2 * np.pi / 60
        pwf_mask = (power < 3500) | (power > 9000)
        df.loc[pwf_mask, "failure"] = 1

        # Overstrain: torque > 60 Nm when tool_wear > 200
        osf_mask = (df["torque"] > 60) & (df["tool_wear"] > 200)
        df.loc[osf_mask, "failure"] = 1

        # Random Failure: 0.1% chance
        rnf_mask = np.random.random(n_samples) < 0.001
        df.loc[rnf_mask, "failure"] = 1

        logger.info(
            "Generated %d samples (%.1f%% failures)",
            n_samples,
            df["failure"].mean() * 100,
        )
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Data cleaning: handle missing values, outliers, duplicates."""

        initial_rows = len(df)

        # Drop exact duplicates
        df = df.drop_duplicates()

        # Handle missing values in feature columns
        for col in FEATURE_COLUMNS:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    # Use median imputation for numeric features
                    df[col] = df[col].fillna(df[col].median())
                    logger.info("Imputed %d missing values in %s", missing, col)

        # Remove extreme outliers (beyond 4 sigma)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != TARGET_COLUMN:
                z_scores = np.abs(stats.zscore(df[col].dropna()))
                outlier_mask = z_scores > 4
                outlier_count = outlier_mask.sum()
                if outlier_count > 0:
                    # Cap at 4 sigma instead of removing
                    upper = df[col].mean() + 4 * df[col].std()
                    lower = df[col].mean() - 4 * df[col].std()
                    df[col] = df[col].clip(lower, upper)
                    logger.info("Capped %d outliers in %s", outlier_count, col)

        cleaned_rows = len(df)
        logger.info(
            "Data cleaning: %d → %d rows (removed %d)",
            initial_rows, cleaned_rows, initial_rows - cleaned_rows,
        )
        return df

    def validate_data(self, df: pd.DataFrame) -> dict:
        """Run data quality checks and return validation report."""
        report = {
            "total_rows": len(df),
            "feature_columns": [],
            "missing_values": {},
            "value_ranges": {},
            "class_distribution": {},
            "passed": True,
            "issues": [],
        }

        # Check required columns
        for col in FEATURE_COLUMNS:
            if col in df.columns:
                report["feature_columns"].append(col)
                report["missing_values"][col] = int(df[col].isna().sum())
                report["value_ranges"][col] = {
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                }
            else:
                report["issues"].append(f"Missing feature column: {col}")
                report["passed"] = False

        # Target distribution
        if TARGET_COLUMN in df.columns:
            dist = df[TARGET_COLUMN].value_counts().to_dict()
            report["class_distribution"] = {str(k): int(v) for k, v in dist.items()}

            # Warn if severe class imbalance
            failure_rate = df[TARGET_COLUMN].mean()
            if failure_rate < 0.01:
                report["issues"].append(
                    f"Severe class imbalance: only {failure_rate:.2%} failures"
                )
        else:
            report["issues"].append("Missing target column: failure")
            report["passed"] = False

        if len(df) < 100:
            report["issues"].append(f"Insufficient data: {len(df)} rows (min 100)")
            report["passed"] = False

        return report

    def prepare_dataset(
        self, filepath: Optional[str] = None
    ) -> Tuple[pd.DataFrame, dict]:
        """Full pipeline: load → clean → validate → return."""
        df = self.load_ai4i_dataset(filepath)
        df = self.clean_data(df)
        validation = self.validate_data(df)

        if not validation["passed"]:
            logger.warning("Data validation issues: %s", validation["issues"])

        return df, validation
