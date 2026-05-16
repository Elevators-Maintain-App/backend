from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_subscriptions import CompanySubscription
from app.db.repositories.subscriptions import company_subscription_repository
from app.services.plans.constants import ACTIVE_SUBSCRIPTION_STATUSES


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_subscription(
        self,
        company_id: UUID,
        on_date: date | None = None,
    ) -> CompanySubscription | None:
        today = on_date or date.today()
        subscriptions = await company_subscription_repository.get_by_company_id(self.db, company_id)

        for subscription in subscriptions:
            if self.is_active(subscription, today):
                return subscription

        return None

    def is_active(self, subscription: CompanySubscription, on_date: date | None = None) -> bool:
        today = on_date or date.today()
        status = (subscription.status or "").lower()

        if status not in ACTIVE_SUBSCRIPTION_STATUSES:
            return False

        if subscription.start_date and subscription.start_date > today:
            return False

        if subscription.end_date and subscription.end_date < today:
            return False

        return True
