from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlanLimitsInput(BaseModel):
    admins: int | None = None
    supervisors: int | None = None
    technicians: int | None = None
    projects: int | None = None
    clients: int | None = None
    units: int | None = None
    work_orders_per_month: int | None = None
    pdf_reports_per_month: int | None = None
    storage_mb: int | None = None


class PlanLimitsResponse(PlanLimitsInput):
    pass


class PlanFeaturesInput(BaseModel):
    offline_mode: bool | None = None
    custom_checklists: bool | None = None
    advanced_dashboard: bool | None = None
    evidence_editing: bool | None = None


class PlanFeaturesResponse(BaseModel):
    offline_mode: bool
    custom_checklists: bool
    advanced_dashboard: bool
    evidence_editing: bool


class PlanCreate(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_public: bool = True
    is_active: bool = True
    limits: PlanLimitsInput = Field(default_factory=PlanLimitsInput)
    features: PlanFeaturesInput = Field(default_factory=PlanFeaturesInput)


class PlanUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    is_active: bool | None = None
    limits: PlanLimitsInput | None = None
    features: PlanFeaturesInput | None = None


class PlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    is_public: bool
    is_active: bool
    limits: PlanLimitsResponse
    features: PlanFeaturesResponse


class PlanBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    max_admins: int | None = None
    max_supervisors: int | None = None
    max_technicians: int | None = None
    max_projects: int | None = None
    max_clients: int | None = None
    max_units: int | None = None
    max_work_orders_per_month: int | None = None
    max_pdf_reports_per_month: int | None = None
    storage_limit_mb: int | None = None
    allow_offline_mode: bool = False
    allow_custom_checklists: bool = False
    allow_advanced_dashboard: bool = False
    allow_evidence_editing: bool = False
    is_public: bool = True
    is_active: bool = True


class PlanRead(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
