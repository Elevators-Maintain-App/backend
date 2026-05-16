from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plans import Plan
from app.db.repositories.plans import plan_repository
from app.services.plans.subscription_service import SubscriptionService


class PlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscription_service = SubscriptionService(db)

    async def get_by_code(self, code: str) -> Plan | None:
        return await plan_repository.get_by_code(self.db, code)

    async def get_active_plan_for_company(
        self,
        company_id: UUID,
        on_date: date | None = None,
    ) -> Plan | None:
        subscription = await self.subscription_service.get_active_subscription(company_id, on_date)
        if subscription is None:
            return None

        plan = subscription.plan
        if plan is None:
            plan = await plan_repository.get(self.db, subscription.plan_id)

        if plan is None or not plan.is_active:
            return None

        return plan
