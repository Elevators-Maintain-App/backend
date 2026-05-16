from app.db.models.plans import Plan
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PlanRepository(CRUDBaseRepository):
    def __init__(self):
        super().__init__(Plan)

    async def get_by_code(self, db: AsyncSession, code: str) -> Plan | None:
        result = await db.execute(select(Plan).where(Plan.code == code))
        return result.scalars().first()

    async def list_plans(self, db: AsyncSession, include_inactive: bool = False) -> list[Plan]:
        query = select(Plan).order_by(Plan.created_at.asc(), Plan.name.asc())
        if not include_inactive:
            query = query.where(Plan.is_active.is_(True))
        result = await db.execute(query)
        return list(result.scalars().all())


plan_repository = PlanRepository()
