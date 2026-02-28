"""
Database Seeder — Initial setup for first deployment.

Creates the first organization, admin user, and equipment.
All credentials are read from environment variables — nothing is hardcoded.

Environment Variables Required:
    SEED_ORG_NAME          — Organization name
    SEED_ORG_SLUG          — URL-safe org slug
    SEED_ADMIN_EMAIL       — Admin user email
    SEED_ADMIN_PASSWORD    — Admin user password (min 10 chars)
    SEED_ADMIN_NAME        — Admin full name
    SEED_ENGINEER_EMAIL    — (optional) Engineer user email
    SEED_ENGINEER_PASSWORD — (optional) Engineer user password
    SEED_ENGINEER_NAME     — (optional) Engineer full name
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.models.organization import Organization, User, UserRole
from app.db.models.equipment import Equipment, EquipmentType, EquipmentStatus
from app.db.models.sensor import SensorReading  # noqa: F401 — needed for relationship resolution
from app.db.models.prediction import Prediction, MLModel, MLTrainingRun  # noqa: F401
from app.db.models.alert import Alert, MaintenanceLog  # noqa: F401

settings = get_settings()


def _require_env(key: str) -> str:
    """Read a required env var or exit with an error."""
    val = os.environ.get(key, "").strip()
    if not val:
        print(f"✗ Missing required environment variable: {key}")
        sys.exit(1)
    return val


async def seed_database():
    """Seed the database with initial organization and admin user from env vars."""

    # ── Read configuration from env ──
    org_name = _require_env("SEED_ORG_NAME")
    org_slug = _require_env("SEED_ORG_SLUG")
    admin_email = _require_env("SEED_ADMIN_EMAIL")
    admin_password = _require_env("SEED_ADMIN_PASSWORD")
    admin_name = _require_env("SEED_ADMIN_NAME")

    if len(admin_password) < 10:
        print("✗ SEED_ADMIN_PASSWORD must be at least 10 characters.")
        sys.exit(1)

    engineer_email = os.environ.get("SEED_ENGINEER_EMAIL", "").strip()
    engineer_password = os.environ.get("SEED_ENGINEER_PASSWORD", "").strip()
    engineer_name = os.environ.get("SEED_ENGINEER_NAME", "").strip()

    engine = create_async_engine(settings.DATABASE_URL)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── Idempotency check: skip if org already exists ──
        existing = await session.execute(
            select(Organization).where(Organization.slug == org_slug)
        )
        if existing.scalar_one_or_none():
            await engine.dispose()
            print(f"✓ Organization '{org_slug}' already exists — nothing to do.")
            return

        # Create organization
        org = Organization(
            name=org_name,
            slug=org_slug,
            description=os.environ.get("SEED_ORG_DESCRIPTION", ""),
            subscription_tier=os.environ.get("SEED_ORG_TIER", "enterprise"),
            max_equipment=int(os.environ.get("SEED_ORG_MAX_EQUIPMENT", "100")),
        )
        session.add(org)
        await session.flush()

        # Create admin user
        admin = User(
            organization_id=org.id,
            email=admin_email,
            hashed_password=hash_password(admin_password),
            full_name=admin_name,
            role=UserRole.ADMIN,
        )
        session.add(admin)

        # Optionally create engineer user
        if engineer_email and engineer_password and engineer_name:
            if len(engineer_password) < 10:
                print("✗ SEED_ENGINEER_PASSWORD must be at least 10 characters.")
                sys.exit(1)
            engineer = User(
                organization_id=org.id,
                email=engineer_email,
                hashed_password=hash_password(engineer_password),
                full_name=engineer_name,
                role=UserRole.ENGINEER,
            )
            session.add(engineer)

        await session.commit()

    await engine.dispose()

    print("✓ Database seeded successfully!")
    print(f"  Organization: {org_name} ({org_slug})")
    print(f"  Admin user: {admin_email}")
    if engineer_email:
        print(f"  Engineer user: {engineer_email}")
    print("  Passwords are NOT logged for security.")
    print("  Register equipment via the API or admin dashboard.")


if __name__ == "__main__":
    asyncio.run(seed_database())
