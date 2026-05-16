from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyUsageRead(BaseModel):
    id: UUID
    company_id: UUID
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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

