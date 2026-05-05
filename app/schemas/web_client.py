from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel


class WebClientInfo(BaseModel):
    id: UUID
    name: str


class WebClientDashboardSummary(BaseModel):
    total_projects: int
    total_units: int
    open_orders: int
    closed_orders: int


class WebClientRecentOrder(BaseModel):
    id: UUID
    reference: str | None = None
    date: dt.date | None = None
    status: str
    unit: str
    project: str


class WebClientDashboard(BaseModel):
    client: WebClientInfo
    summary: WebClientDashboardSummary
    recent_orders: list[WebClientRecentOrder]
