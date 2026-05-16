from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.plans.constants import (
    FEATURE_FIELDS,
    PLAN_LIMIT_REACHED_CODE,
    RESOURCE_LABELS,
    RESOURCE_LIMIT_FIELDS,
)
from app.services.plans.dtos import LimitCheckResult
from app.services.plans.exceptions import InvalidPlanFeatureError, InvalidPlanResourceError
from app.services.plans.plan_service import PlanService


class PlanLimitService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.plan_service = PlanService(db)

    async def get_limit(self, company_id: UUID, resource: str) -> int | None:
        field_name = self._get_resource_field(resource)
        plan = await self.plan_service.get_active_plan_for_company(company_id)
        if plan is None:
            return None

        return getattr(plan, field_name)

    async def is_feature_enabled(self, company_id: UUID, feature: str) -> bool:
        field_name = self._get_feature_field(feature)
        plan = await self.plan_service.get_active_plan_for_company(company_id)
        if plan is None:
            return False

        return bool(getattr(plan, field_name))

    async def check_limit(
        self,
        company_id: UUID,
        resource: str,
        current_usage: int | float,
    ) -> LimitCheckResult:
        plan_limit = await self.get_limit(company_id, resource)

        if plan_limit is None:
            return LimitCheckResult(
                allowed=True,
                resource=resource,
                current_usage=current_usage,
                plan_limit=None,
            )

        allowed = current_usage < plan_limit
        if allowed:
            return LimitCheckResult(
                allowed=True,
                resource=resource,
                current_usage=current_usage,
                plan_limit=plan_limit,
            )

        label = RESOURCE_LABELS.get(resource, resource)
        return LimitCheckResult(
            allowed=False,
            resource=resource,
            current_usage=current_usage,
            plan_limit=plan_limit,
            code=PLAN_LIMIT_REACHED_CODE,
            message=f"Has alcanzado el limite de {label} de tu plan actual.",
        )

    def _get_resource_field(self, resource: str) -> str:
        try:
            return RESOURCE_LIMIT_FIELDS[resource]
        except KeyError as exc:
            raise InvalidPlanResourceError(resource) from exc

    def _get_feature_field(self, feature: str) -> str:
        try:
            return FEATURE_FIELDS[feature]
        except KeyError as exc:
            raise InvalidPlanFeatureError(feature) from exc
