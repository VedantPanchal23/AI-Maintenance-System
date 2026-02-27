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

from slowapi import _rate_limit_exceeded_handler
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
    except Exception as e:
        logger.warning("ML model not available at startup: %s", str(e))

    app.state.model_service = model_service

    # Start simulation if enabled
    if settings.SIMULATION_ENABLED:
        from app.services.simulation import SimulationEngine
        sim_engine = SimulationEngine()

        # Register equipment from DB, or use defaults for demo
        try:
            from app.db.session import async_session_factory
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
            logger.warning("Could not load equipment from DB: %s. Using demo defaults.", e)

        # Fallback: register demo equipment if none found
        if not sim_engine.simulators:
            import uuid as _uuid
            demo_types = ["air_compressor", "pump", "electric_motor", "hvac_chiller"]
            for i, eq_type in enumerate(demo_types):
                sim_engine.register_equipment(
                    equipment_id=str(_uuid.uuid4()),
                    equipment_type=eq_type,
                    initial_wear=i * 30,
                )
            logger.info("Registered %d demo equipment for simulation", len(demo_types))

        # Connect simulation to WebSocket broadcast
        from app.services.websocket import broadcast_sensor_readings
        sim_engine.add_listener(broadcast_sensor_readings)

        app.state.simulation_engine = sim_engine
        asyncio.create_task(sim_engine.start())
        logger.info("Simulation engine started with %d equipment", len(sim_engine.simulators))

    yield

    # ── Shutdown ──
    logger.info("Shutting down %s", settings.APP_NAME)
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
            allowed_hosts=["*.predictive-maintenance.com", "localhost"],
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
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        }

    return app


app = create_application()
