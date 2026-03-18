"""Upgrade a user to ADMIN role — one-time script for demo preparation."""
import asyncio, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import text, update, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import get_settings
from app.db.models.organization import User, UserRole

settings = get_settings()


async def upgrade_to_admin(email: str):
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            print(f"User '{email}' not found!")
            await engine.dispose()
            return

        print(f"Current role: {user.role.value}")
        user.role = UserRole.ADMIN
        await session.commit()
        print(f"Upgraded '{email}' to ADMIN")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(upgrade_to_admin("vedant@predictive-maint.com"))
