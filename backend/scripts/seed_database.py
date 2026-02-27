"""
Database Seeder — Populates initial data for development/demo.

Creates:
- Default organization
- Admin and engineer users
- Sample equipment (4 types)
"""

import asyncio
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


DEMO_EQUIPMENT = [
    {
        "name": "Air Compressor AC-001",
        "equipment_type": EquipmentType.AIR_COMPRESSOR,
        "location": "Building A - Production Floor",
        "manufacturer": "Atlas Copco",
        "model_number": "GA 37+",
        "serial_number": "AC-2024-001",
        "rated_power_kw": 37.0,
        "max_rpm": 1500,
    },
    {
        "name": "Air Compressor AC-002",
        "equipment_type": EquipmentType.AIR_COMPRESSOR,
        "location": "Building A - Utility Room",
        "manufacturer": "Ingersoll Rand",
        "model_number": "R-Series 45",
        "serial_number": "AC-2024-002",
        "rated_power_kw": 45.0,
        "max_rpm": 1800,
    },
    {
        "name": "Centrifugal Pump P-001",
        "equipment_type": EquipmentType.PUMP,
        "location": "Building B - Water Treatment",
        "manufacturer": "Grundfos",
        "model_number": "NB 50-200",
        "serial_number": "PU-2024-001",
        "rated_power_kw": 15.0,
        "max_rpm": 2900,
    },
    {
        "name": "Transfer Pump P-002",
        "equipment_type": EquipmentType.PUMP,
        "location": "Building B - Chemical Processing",
        "manufacturer": "KSB",
        "model_number": "Etanorm 50-160",
        "serial_number": "PU-2024-002",
        "rated_power_kw": 11.0,
        "max_rpm": 2900,
    },
    {
        "name": "Electric Motor EM-001",
        "equipment_type": EquipmentType.ELECTRIC_MOTOR,
        "location": "Building A - Line 1",
        "manufacturer": "Siemens",
        "model_number": "1LE1 Series",
        "serial_number": "EM-2024-001",
        "rated_power_kw": 22.0,
        "max_rpm": 1800,
    },
    {
        "name": "Electric Motor EM-002",
        "equipment_type": EquipmentType.ELECTRIC_MOTOR,
        "location": "Building A - Line 2",
        "manufacturer": "ABB",
        "model_number": "M3BP 200MLA",
        "serial_number": "EM-2024-002",
        "rated_power_kw": 30.0,
        "max_rpm": 1500,
    },
    {
        "name": "HVAC Chiller CH-001",
        "equipment_type": EquipmentType.HVAC_CHILLER,
        "location": "Building C - HVAC Plant Room",
        "manufacturer": "Carrier",
        "model_number": "30XA 252",
        "serial_number": "CH-2024-001",
        "rated_power_kw": 85.0,
        "max_rpm": 1200,
    },
    {
        "name": "HVAC Chiller CH-002",
        "equipment_type": EquipmentType.HVAC_CHILLER,
        "location": "Building D - Clean Room HVAC",
        "manufacturer": "Trane",
        "model_number": "RTAF 300",
        "serial_number": "CH-2024-002",
        "rated_power_kw": 100.0,
        "max_rpm": 1200,
    },
    {
        "name": "Air Compressor AC-003",
        "equipment_type": EquipmentType.AIR_COMPRESSOR,
        "location": "Building D - Packaging Area",
        "manufacturer": "Kaeser",
        "model_number": "ASD 40 S",
        "serial_number": "AC-2024-003",
        "rated_power_kw": 22.0,
        "max_rpm": 1500,
    },
    {
        "name": "Booster Pump P-003",
        "equipment_type": EquipmentType.PUMP,
        "location": "Building C - Boiler Room",
        "manufacturer": "Wilo",
        "model_number": "CronoBloc BL",
        "serial_number": "PU-2024-003",
        "rated_power_kw": 7.5,
        "max_rpm": 2900,
    },
]


async def seed_database():
    """Seed the database with demo data."""
    engine = create_async_engine(settings.DATABASE_URL)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── Idempotency check: skip if org already exists ──
        existing = await session.execute(
            select(Organization).where(Organization.slug == "zydus-pharma-oncology")
        )
        if existing.scalar_one_or_none():
            await engine.dispose()
            print("✓ Database already seeded — nothing to do.")
            return

        # Create organization
        org = Organization(
            name="Zydus Pharma Oncology Pvt. Ltd.",
            slug="zydus-pharma-oncology",
            description="Pharmaceutical manufacturing — oncology division",
            subscription_tier="enterprise",
            max_equipment=100,
        )
        session.add(org)
        await session.flush()

        # Create admin user
        admin = User(
            organization_id=org.id,
            email="admin@zydus-pharma.com",
            hashed_password=hash_password("admin123456"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
        )
        session.add(admin)

        # Create engineer user
        engineer = User(
            organization_id=org.id,
            email="engineer@zydus-pharma.com",
            hashed_password=hash_password("engineer123456"),
            full_name="Maintenance Engineer",
            role=UserRole.ENGINEER,
        )
        session.add(engineer)

        # Create equipment
        for eq_data in DEMO_EQUIPMENT:
            equipment = Equipment(
                organization_id=org.id,
                operating_hours=float(uuid.uuid4().int % 10000),
                **eq_data,
            )
            session.add(equipment)

        await session.commit()

    await engine.dispose()

    print("✓ Database seeded successfully!")
    print(f"  Organization: {org.name}")
    print(f"  Admin: admin@zydus-pharma.com / admin123456")
    print(f"  Engineer: engineer@zydus-pharma.com / engineer123456")
    print(f"  Equipment: {len(DEMO_EQUIPMENT)} units created")


if __name__ == "__main__":
    asyncio.run(seed_database())
