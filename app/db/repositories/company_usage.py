from app.db.models.company_usage import CompanyUsage
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CompanyUsageRepository(CRUDBaseRepository):
    def __init__(self):
        super().__init__(CompanyUsage)

    async def get_by_company_period(
        self,
        db: AsyncSession,
        company_id,
        period_year: int,
        period_month: int,
    ) -> CompanyUsage | None:
        result = await db.execute(
            select(CompanyUsage).where(
                CompanyUsage.company_id == company_id,
                CompanyUsage.period_year == period_year,
                CompanyUsage.period_month == period_month,
            )
        )
        return result.scalars().first()


company_usage_repository = CompanyUsageRepository()
