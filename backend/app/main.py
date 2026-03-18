"""
FastAPI Application Factory

Creates and configures the FastAPI application with all middleware,
routers, event handlers, and exception handlers.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.db.session import engine, async_session_factory
from app.core.exceptions import register_exception_handlers
from app.middleware.tenant import TenantMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

from slowapi.errors import RateLimitExceeded

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application startup and shutdown events."""
    # ── Startup ──
    setup_logging()
    logger.info(
        "Starting %s v%s [env=%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )

    # Initialize ML model cache
    from app.ml.inference import ModelInferenceService
    model_service = ModelInferenceService()
    try:
        await model_service.load_default_model()
        logger.info("ML model loaded successfully")

        # Link to DB record if available
        try:
            from app.db.models.prediction import MLModel
            async with async_session_factory() as session:
                from sqlalchemy import select as _sel
                row = await session.execute(
                    _sel(MLModel.id).where(
                        MLModel.model_path == model_service.model_info.get("model_path")
                    )
                )
                ml_id = row.scalar_one_or_none()
                if ml_id:
                    model_service.model_info["db_id"] = ml_id
        except Exception:
            pass  # DB linkage is non-critical at startup
    except Exception as e:
        logger.warning("ML model not available at startup: %s", str(e))

    app.state.model_service = model_service

    # Start simulation if enabled
    if settings.SIMULATION_ENABLED:
        from app.services.simulation import SimulationEngine
        from app.db.session import async_session_factory

        # Pass model_service + session_factory so simulation can auto-predict
        sim_engine = SimulationEngine(
            model_service=model_service,
            session_factory=async_session_factory,
        )

        # Register equipment from DB
        try:
            from app.db.models.equipment import Equipment
            from sqlalchemy import select

            async with async_session_factory() as session:
                result = await session.execute(
                    select(Equipment.id, Equipment.equipment_type, Equipment.operating_hours)
                    .where(Equipment.is_active == True)
                )
                rows = result.all()
                for row in rows:
                    eq_type = row.equipment_type.value if hasattr(row.equipment_type, 'value') else row.equipment_type
                    sim_engine.register_equipment(
                        equipment_id=str(row.id),
                        equipment_type=eq_type,
                        initial_wear=int(row.operating_hours or 0) % 241,
                    )
                logger.info("Registered %d equipment from DB for simulation", len(rows))
        except Exception as e:
            logger.error("Could not load equipment from DB: %s. Simulation will not start without real equipment.", e)

        if not sim_engine.simulators:
            logger.warning(
                "No equipment found in database. Simulation disabled. "
                "Register equipment via the API to enable real-time monitoring."
            )
            yield
            logger.info("Shutting down %s", settings.APP_NAME)
            from app.db.session import engine
            await engine.dispose()
            return

        # Connect simulation to WebSocket broadcast
        from app.services.websocket import broadcast_sensor_readings
        sim_engine.add_listener(broadcast_sensor_readings)

        app.state.simulation_engine = sim_engine
        asyncio.create_task(sim_engine.start(interval_seconds=10))
        logger.info(
            "Simulation engine started with %d equipment (auto-prediction every 10s)",
            len(sim_engine.simulators),
        )

    # Initialize Redis
    from app.db.redis import init_redis
    await init_redis()

    yield

    # ── Shutdown ──
    logger.info("Shutting down %s", settings.APP_NAME)

    # Close Redis
    from app.db.redis import close_redis
    await close_redis()

    # Stop simulation engine if running
    sim = getattr(app.state, "simulation_engine", None)
    if sim:
        await sim.stop()

    from app.db.session import engine
    await engine.dispose()


def create_application() -> FastAPI:
    """Application factory — creates configured FastAPI instance."""
    app = FastAPI(
        title="AI Predictive Maintenance API",
        description=(
            "Production-grade API for equipment failure prediction "
            "in pharmaceutical manufacturing environments."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost first) ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TenantMiddleware)

    if settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # ── Exception Handlers ──
    register_exception_handlers(app)

    # ── Rate Limiting ──
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # ── Routes ──
    app.include_router(api_router, prefix="/api/v1")

    # ── WebSocket ──
    from app.services.websocket import router as ws_router
    app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

    # ── Health Check ──
    @app.get("/health", tags=["Health"])
    async def health_check():
        import platform

        # Database connectivity
        db_status = "unknown"
        try:
            from app.db.session import async_session_factory
            from sqlalchemy import text
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                db_status = "connected"
        except Exception:
            db_status = "disconnected"

        # GPU detection
        gpu_info = None
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                cuda_version = torch.version.cuda or "unknown"
                gpu_info = f"{gpu_name} {gpu_mem:.0f}GB (CUDA {cuda_version})"
        except ImportError:
            pass

        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "database": db_status,
            "gpu": gpu_info,
            "python_version": platform.python_version(),
            "simulation_enabled": settings.SIMULATION_ENABLED,
        }

    return app


app = create_application()
