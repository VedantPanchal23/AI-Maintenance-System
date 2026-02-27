"""
ML Administration Endpoints

POST /ml/train           — Trigger model training
GET  /ml/models          — List available models
POST /ml/models/load     — Load a specific model
GET  /ml/models/active   — Get currently active model info
"""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_admin, get_db
from app.api.v1.schemas import MLModelInfo, TrainModelRequest, TrainingResultResponse
from app.config import get_settings
from app.core.exceptions import MLModelException
from app.db.models.organization import User
from app.ml.training import TrainingPipeline
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/train", response_model=TrainingResultResponse)
@limiter.limit("3/hour")
async def train_model(
    request: Request,
    body: TrainModelRequest,
    user: User = Depends(get_current_admin),
):
    """
    Trigger ML model training.

    Requires admin role. Trains on synthetic or uploaded data.
    Returns training metrics and model path.
    """
    pipeline = TrainingPipeline()

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
    user: User = Depends(get_current_admin),
):
    """Train all configured algorithms and return comparative results."""
    pipeline = TrainingPipeline()

    try:
        results = await asyncio.to_thread(pipeline.train_all_models)
    except Exception as e:
        raise MLModelException(f"Training failed: {str(e)}")

    return {
        "models_trained": len([r for r in results if "metrics" in r]),
        "results": results,
    }


class LoadModelRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_path: str


@router.get("/models")
async def list_models(
    user: User = Depends(get_current_admin),
):
    """List all saved model artifacts on disk."""
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
    user: User = Depends(get_current_admin),
):
    """Load a specific model artifact into the inference service."""
    model_service = fastapi_request.app.state.model_service

    try:
        await model_service.load_model(request.model_path)
    except FileNotFoundError:
        raise MLModelException(f"Model file not found: {request.model_path}")

    return {
        "status": "loaded",
        "model_info": model_service.model_info,
    }


@router.get("/models/active", response_model=MLModelInfo)
async def get_active_model(
    fastapi_request: Request,
    user: User = Depends(get_current_admin),
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
    user: User = Depends(get_current_admin),
):
    """
    Get model monitoring report — drift detection, prediction stats,
    confidence tracking, and drift alerts.
    """
    from app.ml.monitoring import get_model_monitor

    monitor = get_model_monitor()
    return monitor.get_monitoring_report()
