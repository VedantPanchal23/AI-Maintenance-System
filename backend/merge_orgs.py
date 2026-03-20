import asyncio
from sqlalchemy import select, update
from app.db.session import async_session_factory
from app.db.models.organization import User, Organization
from app.db.models.equipment import Equipment

async def main():
    async with async_session_factory() as session:
        # Find all organizations and count their equipment
        orgs_result = await session.execute(select(Organization))
        orgs = orgs_result.scalars().all()
        
        target_org = None
        max_eq = -1
        
        for org in orgs:
            eq_count_result = await session.execute(select(Equipment).where(Equipment.organization_id == org.id))
            eq_count = len(eq_count_result.scalars().all())
            print(f"Org '{org.name}' has {eq_count} equipments.")
            if eq_count > max_eq:
                max_eq = eq_count
                target_org = org
                
        if target_org:
            print(f"\nTarget Organization with most equipment: {target_org.name}")
            # Move all users to this organization
            await session.execute(
                update(User).values(organization_id=target_org.id)
            )
            # Move all equipment to this organization just in case
            await session.execute(
                update(Equipment).values(organization_id=target_org.id)
            )
            await session.commit()
            print("All users and equipment have been merged into the Target Organization!")

if __name__ == "__main__":
    asyncio.run(main())
