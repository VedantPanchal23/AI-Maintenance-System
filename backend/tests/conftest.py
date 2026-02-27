"""
Pytest configuration and shared fixtures.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.models.organization import Organization, User, UserRole


# ── Test Settings Override ────────────────────────────────────
def get_test_settings():
    return Settings(
        APP_ENV="testing",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5433,
        POSTGRES_DB="predictive_maintenance",
        POSTGRES_USER="pmuser",
        POSTGRES_PASSWORD="pmpass123",
        JWT_SECRET_KEY="test-secret-key-for-unit-testing",
        SIMULATION_ENABLED=False,
        LOG_LEVEL="WARNING",
    )


# ── Async event loop ─────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Database engine and session ───────────────────────────────
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    settings = get_test_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


# ── Test users and org ────────────────────────────────────────
@pytest.fixture
def test_org_id():
    return uuid.uuid4()


@pytest.fixture
def test_admin_user(test_org_id):
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.organization_id = test_org_id
    user.email = "testadmin@test.com"
    user.full_name = "Test Admin"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.hashed_password = hash_password("testpass123")
    user.last_login = None
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def test_engineer_user(test_org_id):
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.organization_id = test_org_id
    user.email = "testengineer@test.com"
    user.full_name = "Test Engineer"
    user.role = UserRole.ENGINEER
    user.is_active = True
    user.hashed_password = hash_password("testpass123")
    user.last_login = None
    user.created_at = datetime.now(timezone.utc)
    return user


# ── HTTP client with app ─────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    """Async HTTP client that talks to the FastAPI app."""
    # Override settings before importing app
    from app.config import get_settings
    import app.config

    original = app.config.get_settings
    app.config.get_settings = get_test_settings
    get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None

    from app.main import create_application

    test_app = create_application()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.config.get_settings = original


# ── Auth tokens ───────────────────────────────────────────────
@pytest.fixture
def admin_token(test_admin_user):
    from app.core.security import create_token_pair

    tokens = create_token_pair(
        user_id=str(test_admin_user.id),
        organization_id=str(test_admin_user.organization_id),
        role=test_admin_user.role.value,
    )
    return tokens["access_token"]


@pytest.fixture
def engineer_token(test_engineer_user):
    from app.core.security import create_token_pair

    tokens = create_token_pair(
        user_id=str(test_engineer_user.id),
        organization_id=str(test_engineer_user.organization_id),
        role=test_engineer_user.role.value,
    )
    return tokens["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
