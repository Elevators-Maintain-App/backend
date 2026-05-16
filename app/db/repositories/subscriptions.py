from app.db.models.company_subscriptions import CompanySubscription
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CompanySubscriptionRepository(CRUDBaseRepository):
    def __init__(self):
        super().__init__(CompanySubscription)

    async def get_by_company_id(
        self,
        db: AsyncSession,
        company_id,
    ) -> list[CompanySubscription]:
        result = await db.execute(
            select(CompanySubscription)
            .options(selectinload(CompanySubscription.plan))
            .where(CompanySubscription.company_id == company_id)
            .order_by(
                CompanySubscription.current_period_start.desc().nullslast(),
                CompanySubscription.start_date.desc().nullslast(),
                CompanySubscription.created_at.desc().nullslast(),
            )
        )
        return list(result.scalars().all())


company_subscription_repository = CompanySubscriptionRepository()
