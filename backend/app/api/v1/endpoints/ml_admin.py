"""
ML Administration Endpoints

POST /ml/train           — Trigger model training
GET  /ml/models          — List available models
POST /ml/models/load     — Load a specific model
GET  /ml/models/active   — Get currently active model info
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_current_engineer_or_admin, get_db
from app.api.v1.schemas import MLModelInfo, TrainModelRequest, TrainingResultResponse
from app.config import get_settings
from app.core.exceptions import MLModelException
from app.db.models.organization import User
from app.db.models.prediction import MLModel, MLTrainingRun
from app.ml.training import TrainingPipeline
from app.middleware.rate_limit import limiter
from app.services.audit import record_audit

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/train", response_model=TrainingResultResponse)
@limiter.limit("3/hour")
async def train_model(
    request: Request,
    body: TrainModelRequest,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger ML model training.

    Requires admin role. Trains on synthetic or uploaded data.
    Returns training metrics and model path.
    """
    pipeline = TrainingPipeline()
    started_at = datetime.now(timezone.utc)

    try:
        result = await asyncio.to_thread(
            pipeline.train_model,
            algorithm=body.algorithm,
            data_filepath=body.data_filepath,
            test_size=body.test_size,
        )
    except Exception as e:
        logger.error("Training failed: %s", str(e))
        raise MLModelException(f"Training failed: {str(e)}")

    # Persist trained model to ml_models table
    ml_model = await _persist_model(db, result)
    # Persist training run to ml_training_runs table
    await _persist_training_run(db, result, ml_model.id, started_at)
    await db.flush()

    await record_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="ml.train_model",
        resource_type="ml_model",
        resource_id=str(ml_model.id),
        details={"algorithm": result["algorithm"], "version": result["version"]},
        ip_address=request.client.host if request.client else None,
    )

    logger.info(
        "Model trained: %s v%s (F1=%.4f)",
        result["algorithm"],
        result["version"],
        result["metrics"]["f1"],
    )

    return TrainingResultResponse(
        run_id=result["run_id"],
        algorithm=result["algorithm"],
        version=result["version"],
        model_path=result["model_path"],
        metrics=result["metrics"],
        training_samples=result["training_samples"],
        test_samples=result["test_samples"],
        training_duration_seconds=result["training_duration_seconds"],
    )


@router.post("/train-all")
async def train_all_models(
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Train all configured algorithms and return comparative results."""
    pipeline = TrainingPipeline()
    started_at = datetime.now(timezone.utc)

    try:
        results = await asyncio.to_thread(pipeline.train_all_models)
    except Exception as e:
        raise MLModelException(f"Training failed: {str(e)}")

    # Persist each successful result to DB
    for result in results:
        if "metrics" not in result:
            continue
        ml_model = await _persist_model(db, result)
        await _persist_training_run(db, result, ml_model.id, started_at)
    await db.flush()

    return {
        "models_trained": len([r for r in results if "metrics" in r]),
        "results": results,
    }


class LoadModelRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_path: str


@router.get("/models")
async def list_models(
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """List registered models from the database."""
    result = await db.execute(
        select(MLModel).order_by(MLModel.created_at.desc())
    )
    db_models = result.scalars().all()

    if db_models:
        return [
            {
                "id": str(m.id),
                "name": m.name,
                "algorithm": m.algorithm,
                "version": m.version,
                "model_path": m.model_path,
                "is_active": m.is_active,
                "is_default": m.is_default,
                "accuracy": m.accuracy,
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
                "auc_roc": m.auc_roc,
                "training_samples": m.training_samples,
                "training_duration_seconds": m.training_duration_seconds,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in db_models
        ]

    # Fallback: scan disk for models not yet registered in DB
    model_dir = Path(settings.ML_MODEL_DIR)
    if not model_dir.exists():
        return []

    models = []
    for f in sorted(model_dir.glob("*.joblib")):
        parts = f.stem.split("_v")
        algorithm = parts[0] if parts else f.stem
        version = parts[1].rsplit("_", 1)[0] if len(parts) > 1 else "unknown"
        models.append({
            "algorithm": algorithm,
            "version": version,
            "model_path": str(f),
            "file_size_mb": round(f.stat().st_size / (1024 * 1024), 2),
        })
    return models


@router.post("/models/load")
async def load_model(
    request: LoadModelRequest,
    fastapi_request: Request,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Load a specific model artifact into the inference service."""
    # Prevent path traversal — resolve and verify within allowed directory
    model_dir = Path(settings.ML_MODEL_DIR).resolve()
    requested_path = Path(request.model_path).resolve()
    if not str(requested_path).startswith(str(model_dir)):
        raise MLModelException("Invalid model path: must be within the model directory")

    model_service = fastapi_request.app.state.model_service

    try:
        await model_service.load_model(str(requested_path))
    except FileNotFoundError:
        raise MLModelException(f"Model file not found: {request.model_path}")

    # Link to DB record if available
    result = await db.execute(
        select(MLModel).where(MLModel.model_path == str(requested_path))
    )
    ml_model = result.scalar_one_or_none()
    if ml_model:
        model_service.model_info["db_id"] = ml_model.id

    await record_audit(
        db,
        user_id=user.id,
        organization_id=user.organization_id,
        action="ml.load_model",
        resource_type="ml_model",
        resource_id=str(requested_path.name),
        details={"model_path": str(requested_path)},
        ip_address=fastapi_request.client.host if fastapi_request.client else None,
    )

    return {
        "status": "loaded",
        "model_info": model_service.model_info,
    }


@router.get("/models/active", response_model=MLModelInfo)
async def get_active_model(
    fastapi_request: Request,
    user: User = Depends(get_current_engineer_or_admin),
):
    """Get info about the currently loaded model."""
    model_service = fastapi_request.app.state.model_service

    if not model_service.is_loaded:
        raise MLModelException("No model is currently loaded")

    info = model_service.model_info
    return MLModelInfo(
        algorithm=info["algorithm"],
        version=info["version"],
        model_path=info["model_path"],
        metrics=info.get("metrics", {}),
        is_loaded=True,
    )


@router.get("/monitoring")
async def get_model_monitoring(
    user: User = Depends(get_current_engineer_or_admin),
):
    """
    Get model monitoring report — drift detection, prediction stats,
    confidence tracking, and drift alerts.
    """
    from app.ml.monitoring import get_model_monitor

    monitor = get_model_monitor()
    return monitor.get_monitoring_report()


@router.post("/models/{model_id}/backtest")
async def backtest_model(
    model_id: str,
    user: User = Depends(get_current_engineer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Run historical backtesting for a model against recent historical data.
    """
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    ml_model = result.scalar_one_or_none()
    if not ml_model:
        raise MLModelException("Model not found")

    def _run_backtest():
        from app.ml.preprocessing import DataPreprocessor
        from app.ml.features import FeatureEngineer
        import joblib
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

        artifact = joblib.load(ml_model.model_path)
        model = artifact["model"]
        scaler = artifact["scaler"]
        
        df, _ = DataPreprocessor().prepare_dataset()
        # Take the last 2000 rows as "recent historical unseen data"
        df = df.tail(2000)
        
        fe = FeatureEngineer()
        fe.scaler = scaler
        fe._is_fitted = True
        
        X, y, _ = fe.prepare_for_training(df)
        
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)
        
        cm = confusion_matrix(y, y_pred)
        
        return {
            "model_id": model_id,
            "samples_tested": len(df),
            "metrics": {
                "accuracy": float(accuracy_score(y, y_pred)),
                "precision": float(precision_score(y, y_pred, zero_division=0)),
                "recall": float(recall_score(y, y_pred, zero_division=0)),
                "f1": float(f1_score(y, y_pred, zero_division=0)),
                "auc_roc": float(roc_auc_score(y, y_proba)),
                "true_positives": int(cm[1, 1]),
                "false_positives": int(cm[0, 1]),
                "true_negatives": int(cm[0, 0]),
                "false_negatives": int(cm[1, 0]),
            }
        }

    try:
        results = await asyncio.to_thread(_run_backtest)
        return results
    except Exception as e:
        logger.error("Backtest failed: %s", e)
        raise MLModelException(f"Backtesting failed: {str(e)}")


# ── Helpers ──────────────────────────────────────────────────────

async def _persist_model(
    db: AsyncSession, result: dict
) -> MLModel:
    """Create an MLModel record from a training result dict."""
    metrics = result["metrics"]

    # Deactivate previous models of the same algorithm
    await db.execute(
        update(MLModel)
        .where(MLModel.algorithm == result["algorithm"], MLModel.is_active.is_(True))
        .values(is_active=False)
    )

    ml_model = MLModel(
        name=f"{result['algorithm']}_{result['version']}",
        version=result["version"],
        algorithm=result["algorithm"],
        model_path=result["model_path"],
        is_active=True,
        accuracy=metrics.get("accuracy"),
        precision=metrics.get("precision"),
        recall=metrics.get("recall"),
        f1_score=metrics.get("f1"),
        auc_roc=metrics.get("auc_roc"),
        training_samples=result.get("training_samples"),
        feature_columns=result.get("feature_columns"),
        hyperparameters=result.get("hyperparameters"),
        training_duration_seconds=result.get("training_duration_seconds"),
    )
    db.add(ml_model)
    await db.flush()
    return ml_model


async def _persist_training_run(
    db: AsyncSession,
    result: dict,
    model_id,
    started_at: datetime,
) -> MLTrainingRun:
    """Create an MLTrainingRun record from a training result dict."""
    metrics = result["metrics"]
    serializable_metrics = {
        k: v for k, v in metrics.items()
        if k not in ("training_history", "confusion_matrix")
    }

    run = MLTrainingRun(
        model_id=model_id,
        algorithm=result["algorithm"],
        status="completed",
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        metrics=serializable_metrics,
        hyperparameters=result.get("hyperparameters"),
        dataset_info={
            "training_samples": result.get("training_samples"),
            "test_samples": result.get("test_samples"),
            "data_validation": result.get("data_validation"),
        },
    )
    db.add(run)
    return run
