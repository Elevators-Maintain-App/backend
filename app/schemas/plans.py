from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PlanBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    max_admins: Optional[int] = None
    max_supervisors: Optional[int] = None
    max_technicians: Optional[int] = None
    max_projects: Optional[int] = None
    max_clients: Optional[int] = None
    max_units: Optional[int] = None
    max_work_orders_per_month: Optional[int] = None
    max_pdf_reports_per_month: Optional[int] = None
    storage_limit_mb: Optional[int] = None
    allow_offline_mode: bool = False
    allow_custom_checklists: bool = False
    allow_advanced_dashboard: bool = False
    allow_evidence_editing: bool = False
    is_public: bool = True
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    max_admins: Optional[int] = None
    max_supervisors: Optional[int] = None
    max_technicians: Optional[int] = None
    max_projects: Optional[int] = None
    max_clients: Optional[int] = None
    max_units: Optional[int] = None
    max_work_orders_per_month: Optional[int] = None
    max_pdf_reports_per_month: Optional[int] = None
    storage_limit_mb: Optional[int] = None
    allow_offline_mode: Optional[bool] = None
    allow_custom_checklists: Optional[bool] = None
    allow_advanced_dashboard: Optional[bool] = None
    allow_evidence_editing: Optional[bool] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class PlanRead(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

