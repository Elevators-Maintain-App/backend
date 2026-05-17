import re
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plans import Plan
from app.db.repositories.plans import plan_repository
from app.db.repositories.subscriptions import company_subscription_repository
from app.schemas.plans import PlanCreate, PlanFeaturesResponse, PlanLimitsResponse, PlanResponse, PlanUpdate
from app.services.plans.constants import FEATURE_FIELDS, RESOURCE_LIMIT_FIELDS
from app.services.plans.exceptions import (
    FreePlanCannotBeDeactivatedError,
    InvalidPlanPayloadError,
    PlanCodeAlreadyExistsError,
    PlanHasActiveSubscriptionsError,
    PlanNotFoundError,
)


PLAN_CODE_PATTERN = re.compile(r"^[a-z0-9_-]+$")


class PlanAdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(self, payload: PlanCreate) -> PlanResponse:
        code = self._normalize_code(payload.code)
        self._validate_required_text(payload.name, "El nombre del plan es requerido.")
        self._validate_limits(payload.limits.model_dump())

        existing = await plan_repository.get_by_code(self.db, code)
        if existing is not None:
            raise PlanCodeAlreadyExistsError()

        plan = Plan(
            code=code,
            name=payload.name.strip(),
            description=self._normalize_optional_text(payload.description),
            is_public=payload.is_public,
            is_active=payload.is_active,
            **self._limit_columns(payload.limits.model_dump()),
            **self._feature_columns(payload.features.model_dump(exclude_unset=True)),
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return self._build_response(plan)

    async def get_plan(self, plan_id: UUID) -> PlanResponse:
        plan = await plan_repository.get(self.db, plan_id)
        if plan is None:
            raise PlanNotFoundError()
        return self._build_response(plan)

    async def update_plan(self, plan_id: UUID, payload: PlanUpdate) -> PlanResponse:
        plan = await plan_repository.get(self.db, plan_id)
        if plan is None:
            raise PlanNotFoundError()

        data = payload.model_dump(exclude_unset=True)

        if "code" in data:
            code = self._normalize_code(payload.code or "")
            existing = await plan_repository.get_by_code_excluding_id(self.db, code, plan_id)
            if existing is not None:
                raise PlanCodeAlreadyExistsError()
            plan.code = code

        if "name" in data:
            self._validate_required_text(payload.name, "El nombre del plan es requerido.")
            plan.name = payload.name.strip()

        if "description" in data:
            plan.description = self._normalize_optional_text(payload.description)

        if "is_public" in data:
            plan.is_public = payload.is_public

        if "is_active" in data:
            if payload.is_active is False:
                await self._assert_plan_can_be_deactivated(plan)
            plan.is_active = payload.is_active

        if payload.limits is not None:
            limits = payload.limits.model_dump(exclude_unset=True)
            self._validate_limits(limits)
            for field, value in self._limit_columns(limits).items():
                setattr(plan, field, value)

        if payload.features is not None:
            for field, value in self._feature_columns(payload.features.model_dump(exclude_unset=True)).items():
                setattr(plan, field, value)

        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return self._build_response(plan)

    async def deactivate_plan(self, plan_id: UUID) -> PlanResponse:
        plan = await plan_repository.get(self.db, plan_id)
        if plan is None:
            raise PlanNotFoundError()

        await self._assert_plan_can_be_deactivated(plan)
        plan.is_active = False
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return self._build_response(plan)

    async def _assert_plan_can_be_deactivated(self, plan: Plan) -> None:
        if plan.code == "free":
            raise FreePlanCannotBeDeactivatedError()

        active_subscriptions = await company_subscription_repository.count_active_by_plan_id(
            self.db,
            plan.id,
            date.today(),
        )
        if active_subscriptions > 0:
            raise PlanHasActiveSubscriptionsError()

    def _normalize_code(self, code: str) -> str:
        normalized = (code or "").strip().lower()
        if not normalized:
            raise InvalidPlanPayloadError("El codigo del plan es requerido.")
        if not PLAN_CODE_PATTERN.fullmatch(normalized):
            raise InvalidPlanPayloadError("El codigo del plan solo puede contener letras minusculas, numeros, guiones y guiones bajos.")
        return normalized

    def _validate_required_text(self, value: str | None, message: str) -> None:
        if value is None or not value.strip():
            raise InvalidPlanPayloadError(message)

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _validate_limits(self, limits: dict) -> None:
        for value in limits.values():
            if value is not None and value < 0:
                raise InvalidPlanPayloadError("Los limites del plan deben ser mayores o iguales a 0, o null para ilimitado.")

    def _limit_columns(self, limits: dict) -> dict:
        return {
            RESOURCE_LIMIT_FIELDS[key]: value
            for key, value in limits.items()
            if key in RESOURCE_LIMIT_FIELDS
        }

    def _feature_columns(self, features: dict) -> dict:
        return {
            FEATURE_FIELDS[key]: value
            for key, value in features.items()
            if key in FEATURE_FIELDS
        }

    def _build_response(self, plan: Plan) -> PlanResponse:
        return PlanResponse(
            id=plan.id,
            code=plan.code,
            name=plan.name,
            description=plan.description,
            is_public=plan.is_public,
            is_active=plan.is_active,
            limits=PlanLimitsResponse(
                admins=plan.max_admins,
                supervisors=plan.max_supervisors,
                technicians=plan.max_technicians,
                projects=plan.max_projects,
                clients=plan.max_clients,
                units=plan.max_units,
                work_orders_per_month=plan.max_work_orders_per_month,
                pdf_reports_per_month=plan.max_pdf_reports_per_month,
                storage_mb=plan.storage_limit_mb,
            ),
            features=PlanFeaturesResponse(
                offline_mode=plan.allow_offline_mode,
                custom_checklists=plan.allow_custom_checklists,
                advanced_dashboard=plan.allow_advanced_dashboard,
                evidence_editing=plan.allow_evidence_editing,
            ),
        )
