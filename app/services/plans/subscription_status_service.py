from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_subscriptions import CompanySubscription
from app.db.models.plans import Plan
from app.db.repositories.compania import compania_crud
from app.db.repositories.plans import plan_repository
from app.schemas.subscriptions import (
    AdminPlanRead,
    CompanySubscriptionStatusResponse,
    CompanyUsageSummary,
    PlanFeaturesSummary,
    PlanLimitsSummary,
    SubscriptionAssignRequest,
    SubscriptionPlanSummary,
    SubscriptionSummary,
)
from app.services.plans.exceptions import PlanInactiveError, PlanNotFoundError, SubscriptionNotFoundError
from app.services.plans.subscription_service import SubscriptionService
from app.services.plans.usage_service import CompanyUsageService


class CompanyNotFoundError(Exception):
    code = "COMPANY_NOT_FOUND"

    def __init__(self):
        self.message = "Compania no encontrada."
        super().__init__(self.message)


class InvalidSubscriptionPeriodError(Exception):
    code = "INVALID_SUBSCRIPTION_PERIOD"

    def __init__(self):
        self.message = "El periodo de suscripcion no es valido."
        super().__init__(self.message)


class SubscriptionStatusService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.subscription_service = SubscriptionService(db)
        self.usage_service = CompanyUsageService(db)

    async def get_company_status(self, company_id: UUID, on_date: date | None = None) -> CompanySubscriptionStatusResponse:
        company = await compania_crud.get(self.db, company_id)
        if company is None:
            raise CompanyNotFoundError()

        subscription = await self.subscription_service.get_active_subscription(company_id, on_date)
        if subscription is None:
            raise SubscriptionNotFoundError()

        plan = subscription.plan or await plan_repository.get(self.db, subscription.plan_id)
        if plan is None:
            raise PlanNotFoundError()
        if not plan.is_active:
            raise PlanInactiveError()

        today = on_date or date.today()
        usage = await self.usage_service.get_or_create_monthly_usage(company_id, today.year, today.month)
        return self._build_status_response(company_id, subscription, plan, usage)

    async def list_plans(self, include_inactive: bool = False) -> list[AdminPlanRead]:
        plans = await plan_repository.list_plans(self.db, include_inactive=include_inactive)
        return [self._build_admin_plan(plan) for plan in plans]

    async def assign_subscription(
        self,
        company_id: UUID,
        payload: SubscriptionAssignRequest,
    ) -> CompanySubscriptionStatusResponse:
        company = await compania_crud.get(self.db, company_id)
        if company is None:
            raise CompanyNotFoundError()

        plan = await plan_repository.get(self.db, payload.plan_id)
        if plan is None:
            raise PlanNotFoundError()
        if not plan.is_active:
            raise PlanInactiveError()

        if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
            raise InvalidSubscriptionPeriodError()

        active_subscription = await self.subscription_service.get_active_subscription(company_id)
        now = datetime.now(timezone.utc)
        if active_subscription is not None:
            active_subscription.status = "cancelled"
            active_subscription.end_date = payload.start_date or date.today()
            active_subscription.cancelled_at = now
            self.db.add(active_subscription)

        subscription = CompanySubscription(
            company_id=company_id,
            plan_id=payload.plan_id,
            status=payload.status,
            billing_period=payload.billing_period,
            start_date=payload.start_date or date.today(),
            end_date=payload.end_date,
            current_period_start=payload.current_period_start,
            current_period_end=payload.current_period_end,
            trial_ends_at=payload.trial_ends_at,
            next_payment_due_at=payload.next_payment_due_at,
            notes=payload.notes,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        subscription.plan = plan

        return await self.get_company_status(company_id)

    def _build_status_response(self, company_id: UUID, subscription, plan: Plan, usage) -> CompanySubscriptionStatusResponse:
        limits = self._build_limits(plan)
        features = self._build_features(plan)
        return CompanySubscriptionStatusResponse(
            company_id=company_id,
            subscription=SubscriptionSummary(
                id=subscription.id,
                status=subscription.status,
                billing_period=subscription.billing_period,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                current_period_start=subscription.current_period_start,
                current_period_end=subscription.current_period_end,
                trial_ends_at=subscription.trial_ends_at,
                next_payment_due_at=subscription.next_payment_due_at,
            ),
            plan=SubscriptionPlanSummary(
                id=plan.id,
                code=plan.code,
                name=plan.name,
                description=plan.description,
                is_public=plan.is_public,
                is_active=plan.is_active,
            ),
            limits=limits,
            features=features,
            usage=CompanyUsageSummary(
                period_year=usage.period_year,
                period_month=usage.period_month,
                users_count=usage.users_count,
                admins_count=usage.admins_count,
                supervisors_count=usage.supervisors_count,
                technicians_count=usage.technicians_count,
                projects_count=usage.projects_count,
                clients_count=usage.clients_count,
                units_count=usage.units_count,
                work_orders_created=usage.work_orders_created,
                pdf_reports_generated=usage.pdf_reports_generated,
                storage_used_mb=usage.storage_used_mb,
            ),
        )

    def _build_admin_plan(self, plan: Plan) -> AdminPlanRead:
        return AdminPlanRead(
            id=plan.id,
            code=plan.code,
            name=plan.name,
            description=plan.description,
            is_public=plan.is_public,
            is_active=plan.is_active,
            limits=self._build_limits(plan),
            features=self._build_features(plan),
        )

    def _build_limits(self, plan: Plan) -> PlanLimitsSummary:
        return PlanLimitsSummary(
            admins=plan.max_admins,
            supervisors=plan.max_supervisors,
            technicians=plan.max_technicians,
            projects=plan.max_projects,
            clients=plan.max_clients,
            units=plan.max_units,
            work_orders_per_month=plan.max_work_orders_per_month,
            pdf_reports_per_month=plan.max_pdf_reports_per_month,
            storage_mb=plan.storage_limit_mb,
        )

    def _build_features(self, plan: Plan) -> PlanFeaturesSummary:
        return PlanFeaturesSummary(
            offline_mode=plan.allow_offline_mode,
            custom_checklists=plan.allow_custom_checklists,
            advanced_dashboard=plan.allow_advanced_dashboard,
            evidence_editing=plan.allow_evidence_editing,
        )
