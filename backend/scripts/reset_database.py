"""
Database Reset — Wipe ALL data, keep schema intact.

This script truncates every data table (CASCADE) so the system
starts completely fresh. The Alembic migration version is preserved.

Usage:
    python -m scripts.reset_database
"""

import asyncio
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings

settings = get_settings()

# Tables to truncate (order doesn't matter with CASCADE)
TABLES_TO_TRUNCATE = [
    "alerts",
    "predictions",
    "sensor_readings",
    "maintenance_logs",
    "audit_logs",
    "equipment",
    "users",
    "ml_training_runs",
    "ml_models",
    "organizations",
]


async def reset_database():
    """Truncate all data tables, keeping schema and alembic_version."""
    engine = create_async_engine(settings.DATABASE_URL)

    print("=" * 50)
    print("DATABASE RESET")
    print(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"DB:   {settings.POSTGRES_DB}")
    print("=" * 50)

    async with engine.begin() as conn:
        for table in TABLES_TO_TRUNCATE:
            try:
                result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                await conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
                print(f"  TRUNCATED {table}: {count} rows removed")
            except Exception as e:
                err_msg = str(e)
                if "does not exist" in err_msg:
                    print(f"  SKIPPED   {table}: table does not exist")
                else:
                    print(f"  ERROR     {table}: {err_msg[:80]}")

    # Verify
    print()
    print("VERIFICATION:")
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        tables = [r[0] for r in result.fetchall()]
        for t in tables:
            try:
                result = await conn.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
                count = result.scalar()
                status = "OK" if (count == 0 or t == "alembic_version") else "NOT EMPTY"
                print(f"  {t}: {count} rows [{status}]")
            except Exception as e:
                print(f"  {t}: ERROR")

    await engine.dispose()
    print()
    print("Database reset complete. All data has been wiped.")
    print("You can now register a fresh user at http://localhost:3000/register")


if __name__ == "__main__":
    asyncio.run(reset_database())
