from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionErrorDetail(BaseModel):
    detail: str
    code: str


class PlanLimitsSummary(BaseModel):
    admins: int | None
    supervisors: int | None
    technicians: int | None
    projects: int | None
    clients: int | None
    units: int | None
    work_orders_per_month: int | None
    pdf_reports_per_month: int | None
    storage_mb: int | None


class PlanFeaturesSummary(BaseModel):
    offline_mode: bool
    custom_checklists: bool
    advanced_dashboard: bool
    evidence_editing: bool


class SubscriptionPlanSummary(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    is_public: bool
    is_active: bool
    limits: PlanLimitsSummary | None = None
    features: PlanFeaturesSummary | None = None


class SubscriptionSummary(BaseModel):
    id: UUID
    status: str
    billing_period: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    current_period_start: date | None = None
    current_period_end: date | None = None
    trial_ends_at: date | None = None
    next_payment_due_at: datetime | None = None


class CompanyUsageSummary(BaseModel):
    period_year: int
    period_month: int
    users_count: int
    admins_count: int
    supervisors_count: int
    technicians_count: int
    projects_count: int
    clients_count: int
    units_count: int
    work_orders_created: int
    pdf_reports_generated: int
    storage_used_mb: int


class CompanySubscriptionStatusResponse(BaseModel):
    company_id: UUID
    subscription: SubscriptionSummary
    plan: SubscriptionPlanSummary
    limits: PlanLimitsSummary
    features: PlanFeaturesSummary
    usage: CompanyUsageSummary


class AdminPlanRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    is_public: bool
    is_active: bool
    limits: PlanLimitsSummary
    features: PlanFeaturesSummary


class SubscriptionAssignRequest(BaseModel):
    plan_id: UUID
    status: str = Field(default="active")
    billing_period: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    current_period_start: date | None = None
    current_period_end: date | None = None
    trial_ends_at: date | None = None
    next_payment_due_at: datetime | None = None
    notes: str | None = None
