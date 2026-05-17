from app.db.models.company_subscriptions import CompanySubscription
from app.db.repositories.base import CRUDBaseRepository
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active", "trial", "trialing"})


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

    async def count_active_by_plan_id(
        self,
        db: AsyncSession,
        plan_id,
        on_date,
    ) -> int:
        result = await db.execute(
            select(func.count())
            .select_from(CompanySubscription)
            .where(
                CompanySubscription.plan_id == plan_id,
                func.lower(CompanySubscription.status).in_(ACTIVE_SUBSCRIPTION_STATUSES),
                or_(CompanySubscription.start_date.is_(None), CompanySubscription.start_date <= on_date),
                or_(CompanySubscription.end_date.is_(None), CompanySubscription.end_date >= on_date),
            )
        )
        return int(result.scalar() or 0)


company_subscription_repository = CompanySubscriptionRepository()
