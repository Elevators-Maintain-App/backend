from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CompanySubscriptionBase(BaseModel):
    company_id: UUID
    plan_id: UUID
    status: str
    billing_period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    trial_ends_at: Optional[date] = None
    last_payment_at: Optional[datetime] = None
    next_payment_due_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: Optional[str] = None


class CompanySubscriptionCreate(CompanySubscriptionBase):
    pass


class CompanySubscriptionUpdate(BaseModel):
    plan_id: Optional[UUID] = None
    status: Optional[str] = None
    billing_period: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    trial_ends_at: Optional[date] = None
    last_payment_at: Optional[datetime] = None
    next_payment_due_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: Optional[str] = None


class CompanySubscriptionRead(CompanySubscriptionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

