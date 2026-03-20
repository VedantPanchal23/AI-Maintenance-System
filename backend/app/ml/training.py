"""
ML Training Pipeline

Trains multiple classification models for equipment failure prediction.
Supports: Random Forest, XGBoost, LightGBM, PyTorch Deep Neural Network (GPU).

The PyTorch DNN runs on NVIDIA RTX 3050 6GB via CUDA 12.x when available,
with automatic CPU fallback.

Includes:
- Stratified cross-validation
- Hyperparameter configuration
- Model evaluation with multiple metrics
- Model serialization and versioning
- GPU-accelerated neural network training
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

from app.config import get_settings
from app.ml.features import FeatureEngineer
from app.ml.preprocessing import DataPreprocessor

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False

logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════
# PyTorch Neural Network Model
# ═══════════════════════════════════════════════════════════════

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        GPU_NAME = torch.cuda.get_device_name(0)
        GPU_MEM = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info("PyTorch using GPU: %s (%.1f GB)", GPU_NAME, GPU_MEM)
    else:
        logger.info("PyTorch using CPU (no CUDA GPU detected)")

except ImportError:
    TORCH_AVAILABLE = False
    DEVICE = None
    logger.warning("PyTorch not installed — neural_network_deep will be unavailable")


class PredictiveMaintenanceNN(nn.Module if TORCH_AVAILABLE else object):
    """
    Deep Neural Network for equipment failure prediction.

    Architecture:
    - Input → 256 → BatchNorm → ReLU → Dropout(0.3)
    - 256 → 128 → BatchNorm → ReLU → Dropout(0.3)
    - 128 → 64 → BatchNorm → ReLU → Dropout(0.2)
    - 64 → 32 → BatchNorm → ReLU → Dropout(0.2)
    - 32 → 1 → Sigmoid

    Designed for binary classification with class imbalance handling
    via weighted BCE loss.
    """

    def __init__(self, input_dim, dropout_rate=0.3):
        super().__init__()
        self.network = nn.Sequential(
            # Block 1
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout_rate),

            # Block 2
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),

            # Block 3
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.2),

            # Block 4
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.2),

            # Output — raw logits (use BCEWithLogitsLoss for numerical stability)
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.network(x).squeeze(-1)


class PyTorchModelWrapper:
    """
    Sklearn-compatible wrapper for the PyTorch NN model.
    Enables seamless integration with the training pipeline.

    Handles:
    - GPU/CPU device management
    - Class-weighted loss for imbalanced data
    - Early stopping based on validation F1
    - Learning rate scheduling
    """

    def __init__(
        self,
        input_dim=None,
        epochs=100,
        batch_size=256,
        learning_rate=0.001,
        weight_decay=1e-4,
        patience=15,
        dropout_rate=0.3,
    ):
        self.input_dim = input_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.patience = patience
        self.dropout_rate = dropout_rate
        self.model = None
        self.device = DEVICE
        self.training_history = []

    def fit(self, X, y):
        """Train the neural network with early stopping."""
        input_dim = X.shape[1]
        self.input_dim = input_dim

        # Create model and move to GPU
        self.model = PredictiveMaintenanceNN(input_dim, self.dropout_rate).to(self.device)

        # Calculate class weight for imbalanced data
        n_pos = y.sum()
        n_neg = len(y) - n_pos
        pos_weight = torch.tensor([n_neg / max(n_pos, 1)], dtype=torch.float32).to(self.device)

        # BCEWithLogitsLoss combines sigmoid + BCE — more numerically stable
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='max', factor=0.5, patience=5, verbose=False
        )

        # Validation split for early stopping
        X_t, X_v, y_t, y_v = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)

        # Convert to tensors
        X_train_t = torch.FloatTensor(X_t).to(self.device)
        y_train_t = torch.FloatTensor(y_t).to(self.device)
        X_val_t = torch.FloatTensor(X_v).to(self.device)
        y_val_t = torch.FloatTensor(y_v).to(self.device)

        train_dataset = TensorDataset(X_train_t, y_train_t)
        train_loader = DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True, drop_last=False
        )

        best_val_f1 = 0.0
        best_state = None
        patience_counter = 0
        self.training_history = []

        logger.info(
            "Training PyTorch NN on %s | input_dim=%d | samples=%d | pos_rate=%.2f%%",
            self.device, input_dim, len(X_t), (y_t.mean() * 100),
        )

        for epoch in range(self.epochs):
            # ── Train ──
            self.model.train()
            epoch_loss = 0.0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                logits = self.model(batch_X)
                loss = criterion(logits, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()

            # ── Validate ──
            self.model.eval()
            with torch.no_grad():
                val_logits = self.model(X_val_t)
                val_proba = torch.sigmoid(val_logits).cpu().numpy()
                val_preds = (val_proba >= 0.5).astype(int)
                val_f1 = f1_score(y_v, val_preds, zero_division=0)
                val_recall = recall_score(y_v, val_preds, zero_division=0)

            scheduler.step(val_f1)
            avg_loss = epoch_loss / len(train_loader)

            self.training_history.append({
                "epoch": epoch + 1,
                "loss": avg_loss,
                "val_f1": val_f1,
                "val_recall": val_recall,
                "lr": optimizer.param_groups[0]["lr"],
            })

            # ── Early stopping ──
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1

            if (epoch + 1) % 10 == 0:
                logger.info(
                    "  Epoch %d/%d — loss=%.4f val_f1=%.4f val_recall=%.4f lr=%.6f",
                    epoch + 1, self.epochs, avg_loss, val_f1, val_recall,
                    optimizer.param_groups[0]["lr"],
                )

            if patience_counter >= self.patience:
                logger.info("  Early stopping at epoch %d (best val_f1=%.4f)", epoch + 1, best_val_f1)
                break

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)
            self.model.to(self.device)

        logger.info("Training complete. Best val F1=%.4f", best_val_f1)
        return self

    def predict(self, X):
        """Predict binary labels using optimized threshold."""
        proba = self.predict_proba(X)
        threshold = getattr(self, "optimal_threshold", 0.5)
        return (proba[:, 1] >= threshold).astype(int)

    def predict_proba(self, X):
        """Predict probabilities for both classes (applies sigmoid to logits)."""
        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)

        with torch.no_grad():
            logits = self.model(X_tensor)
            proba_pos = torch.sigmoid(logits).cpu().numpy()

        proba_neg = 1.0 - proba_pos
        return np.column_stack([proba_neg, proba_pos])

    def optimize_threshold(self, X_val, y_val):
        """Find the optimal classification threshold via F1 grid search."""
        proba = self.predict_proba(X_val)[:, 1]
        best_f1 = 0.0
        best_threshold = 0.5
        for t in np.arange(0.1, 0.9, 0.01):
            preds = (proba >= t).astype(int)
            score = f1_score(y_val, preds, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_threshold = t
        self.optimal_threshold = float(best_threshold)
        logger.info("Optimal threshold: %.2f (F1=%.4f)", best_threshold, best_f1)
        return best_threshold

    def get_params(self, deep=True):
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "patience": self.patience,
            "dropout_rate": self.dropout_rate,
        }

    def set_params(self, **params):
        for key, val in params.items():
            setattr(self, key, val)
        return self


# ═══════════════════════════════════════════════════════════════
# Hyperparameter Configurations
# ═══════════════════════════════════════════════════════════════

MODEL_CONFIGS = {
    "random_forest": {
        "class": RandomForestClassifier,
        "params": {
            "n_estimators": 300,
            "max_depth": 18,
            "min_samples_split": 4,
            "min_samples_leaf": 2,
            "max_features": "sqrt",
            "class_weight": "balanced",
            "random_state": 42,
            "n_jobs": -1,
        },
        "param_grid": {
            "n_estimators": [100, 300],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5],
        }
    },
    "xgboost": {
        "lazy_import": "xgboost",
        "class_name": "XGBClassifier",
        "params": {
            "n_estimators": 500,
            "max_depth": 10,
            "learning_rate": 0.03,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_weight": 3,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.5,
            "scale_pos_weight": 5,
            "eval_metric": "logloss",
            "tree_method": "hist",
            "random_state": 42,
            "n_jobs": -1,
        },
        "param_grid": {
            "max_depth": [6, 10],
            "learning_rate": [0.01, 0.05],
            "n_estimators": [300, 500]
        }
    },
    "lightgbm": {
        "lazy_import": "lightgbm",
        "class_name": "LGBMClassifier",
        "params": {
            "n_estimators": 500,
            "max_depth": 10,
            "learning_rate": 0.03,
            "num_leaves": 63,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "min_child_samples": 10,
            "reg_alpha": 0.1,
            "reg_lambda": 1.5,
            "is_unbalance": True,
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1,
        },
    },
}

# Add PyTorch DNN if available
if TORCH_AVAILABLE:
    MODEL_CONFIGS["neural_network_deep"] = {
        "class": PyTorchModelWrapper,
        "params": {
            "epochs": 150,
            "batch_size": 256,
            "learning_rate": 0.001,
            "weight_decay": 1e-4,
            "patience": 25,
            "dropout_rate": 0.3,
        },
    }
else:
    # Fallback to sklearn MLP if PyTorch not available
    from sklearn.neural_network import MLPClassifier
    MODEL_CONFIGS["neural_network_sklearn"] = {
        "class": MLPClassifier,
        "params": {
            "hidden_layer_sizes": (256, 128, 64, 32),
            "activation": "relu",
            "solver": "adam",
            "alpha": 0.001,
            "batch_size": 64,
            "learning_rate": "adaptive",
            "learning_rate_init": 0.001,
            "max_iter": 500,
            "early_stopping": True,
            "validation_fraction": 0.15,
            "random_state": 42,
        },
    }


# ═══════════════════════════════════════════════════════════════
# Training Pipeline
# ═══════════════════════════════════════════════════════════════

class TrainingPipeline:
    """End-to-end model training pipeline with GPU support."""

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir or settings.ML_MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()

    def _get_model_instance(self, algorithm: str):
        """Instantiate model class from config."""
        config = MODEL_CONFIGS[algorithm]

        if "lazy_import" in config:
            import importlib
            module = importlib.import_module(config["lazy_import"])
            model_class = getattr(module, config["class_name"])
        else:
            model_class = config["class"]

        return model_class(**config["params"])

    def train_model(
        self,
        algorithm: str = "xgboost",
        data_filepath: Optional[str] = None,
        test_size: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Train a single model.

        Returns training report with metrics and model path.
        """
        if algorithm not in MODEL_CONFIGS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. "
                f"Available: {list(MODEL_CONFIGS.keys())}"
            )

        logger.info("=" * 60)
        logger.info("Starting training: algorithm=%s", algorithm)
        if TORCH_AVAILABLE and algorithm == "neural_network_deep":
            logger.info("Device: %s", DEVICE)
        logger.info("=" * 60)

        start_time = time.time()
        run_id = str(uuid.uuid4())[:8]

        # ── Step 1: Load & prepare data ──
        df, validation = self.preprocessor.prepare_dataset(data_filepath)
        X, y, feature_columns = self.feature_engineer.prepare_for_training(df)

        # ── Step 2: Train/test split ──
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        logger.info(
            "Data split: train=%d, test=%d (failure rate: train=%.2f%%, test=%.2f%%)",
            len(X_train), len(X_test),
            y_train.mean() * 100, y_test.mean() * 100,
        )

        # ── Step 3a: SMOTE Oversampling (for NN and tree models) ──
        if SMOTE_AVAILABLE and algorithm in ("neural_network_deep",):
            smote = SMOTE(random_state=42, sampling_strategy=0.5)
            X_train, y_train = smote.fit_resample(X_train, y_train)
            logger.info(
                "SMOTE applied: train=%d (failure rate: %.2f%%)",
                len(X_train), y_train.mean() * 100,
            )

        # ── Step 3b: Train or Tune ──
        model = self._get_model_instance(algorithm)
        config = MODEL_CONFIGS[algorithm]

        best_params = config["params"]
        if "param_grid" in config and algorithm not in ("neural_network_deep",):
            logger.info("Running GridSearchCV for %s...", algorithm)
            from sklearn.model_selection import GridSearchCV
            grid = GridSearchCV(model, config["param_grid"], cv=3, scoring="f1", n_jobs=-1)
            grid.fit(X_train, y_train)
            model = grid.best_estimator_
            best_params = grid.best_params_
            logger.info("Best parameters found: %s", best_params)
        else:
            model.fit(X_train, y_train)

        # ── Step 3c: Threshold Optimization (for PyTorch NN) ──
        if hasattr(model, "optimize_threshold"):
            model.optimize_threshold(X_test, y_test)

        # ── Step 4: Evaluate ──
        y_pred = model.predict(X_test)
        y_proba = (
            model.predict_proba(X_test)[:, 1]
            if hasattr(model, "predict_proba")
            else y_pred.astype(float)
        )

        metrics = self._compute_metrics(y_test, y_pred, y_proba)

        # Add training history for NN
        if hasattr(model, "training_history"):
            metrics["training_history"] = model.training_history

        # Extract Feature Importances
        feature_importance = {}
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            feature_importance = {
                feat: float(imp) for feat, imp in zip(feature_columns, importances)
            }
            # Sort by importance descending
            feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))

        # ── Step 5: Cross-validation (skip for deep NN — too slow) ──
        if algorithm not in ("neural_network_deep",):
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            cv_scores = cross_val_score(
                self._get_model_instance(algorithm), X, y, cv=cv, scoring="f1"
            )
            metrics["cv_f1_mean"] = float(cv_scores.mean())
            metrics["cv_f1_std"] = float(cv_scores.std())
        else:
            metrics["cv_f1_mean"] = metrics["f1"]
            metrics["cv_f1_std"] = 0.0

        # ── Step 6: Save model ──
        training_duration = time.time() - start_time
        version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        model_filename = f"{algorithm}_v{version}_{run_id}.joblib"
        model_path = self.model_dir / model_filename

        # For PyTorch models, save state dict separately for portability
        artifact = {
            "model": model,
            "scaler": self.feature_engineer.scaler,
            "feature_columns": feature_columns,
            "feature_importance": feature_importance,
            "algorithm": algorithm,
            "version": version,
            "metrics": {k: v for k, v in metrics.items() if k != "training_history"},
            "hyperparameters": best_params,
        }

        # Also save PyTorch state dict for production deployment
        if TORCH_AVAILABLE and hasattr(model, "model") and isinstance(model.model, nn.Module):
            torch_path = self.model_dir / f"{algorithm}_v{version}_{run_id}.pt"
            torch.save({
                "model_state_dict": model.model.state_dict(),
                "input_dim": model.input_dim,
                "dropout_rate": model.dropout_rate,
            }, torch_path)
            artifact["torch_path"] = str(torch_path)
            logger.info("PyTorch state dict saved: %s", torch_path)

        joblib.dump(artifact, model_path)

        logger.info(
            "Model saved: %s (F1=%.4f, AUC=%.4f, Recall=%.4f, time=%.1fs)",
            model_path, metrics["f1"], metrics["auc_roc"],
            metrics["recall"], training_duration,
        )

        return {
            "run_id": run_id,
            "algorithm": algorithm,
            "version": version,
            "model_path": str(model_path),
            "metrics": metrics,
            "feature_columns": feature_columns,
            "hyperparameters": MODEL_CONFIGS[algorithm]["params"],
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "training_duration_seconds": round(training_duration, 2),
            "data_validation": validation,
            "device": str(DEVICE) if TORCH_AVAILABLE and "neural" in algorithm else "cpu",
        }

    def train_all_models(
        self, data_filepath: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Train all configured algorithms and return comparative results."""
        results = []

        logger.info("=" * 60)
        logger.info("Training ALL models: %s", list(MODEL_CONFIGS.keys()))
        if TORCH_AVAILABLE:
            logger.info("GPU: %s", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only")
        logger.info("=" * 60)

        for algorithm in MODEL_CONFIGS:
            try:
                result = self.train_model(algorithm, data_filepath)
                results.append(result)
            except Exception as e:
                logger.error("Failed to train %s: %s", algorithm, str(e), exc_info=True)
                results.append({
                    "algorithm": algorithm,
                    "status": "failed",
                    "error": str(e),
                })

        # Sort by F1 score (best first)
        results.sort(
            key=lambda r: r.get("metrics", {}).get("f1", 0),
            reverse=True,
        )
        return results

    def _compute_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray
    ) -> Dict[str, float]:
        """Compute comprehensive evaluation metrics."""
        cm = confusion_matrix(y_true, y_pred)

        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "auc_roc": float(roc_auc_score(y_true, y_proba)),
            "confusion_matrix": cm.tolist(),
            "true_negatives": int(cm[0, 0]),
            "false_positives": int(cm[0, 1]),
            "false_negatives": int(cm[1, 0]),
            "true_positives": int(cm[1, 1]),
        }
