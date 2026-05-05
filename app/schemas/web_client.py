from __future__ import annotations

import datetime as dt
from math import ceil
from uuid import UUID

from pydantic import BaseModel, Field


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


class WebClientUnitItem(BaseModel):
    id: UUID
    name: str
    project_id: UUID
    project: str
    type: str | None = None
    kpi_functioning: str | None = None


class WebClientUnitDetail(WebClientUnitItem):
    company_id: UUID
    client_id: UUID
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


class WebClientOrderItem(BaseModel):
    id: UUID
    reference: str | None = None
    date: dt.date | None = None
    status: str
    project_id: UUID
    project: str
    unit_id: UUID
    unit: str
    type: str | None = None
    priority: str | None = None
    has_report: bool = False


class WebClientOrderDetail(WebClientOrderItem):
    description: str | None = None
    observations: str | None = None
    technician: str | None = None
    supervisor: str | None = None
    final_report_url: str | None = None


class WebClientReportLink(BaseModel):
    report_url: str


class WebClientPage(BaseModel):
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)

    @classmethod
    def page_count(cls, total: int, page_size: int) -> int:
        return ceil(total / page_size) if total else 0


class WebClientUnitsPage(WebClientPage):
    data: list[WebClientUnitItem]

    @classmethod
    def create(
        cls,
        *,
        data: list[WebClientUnitItem],
        total: int,
        page: int,
        page_size: int,
    ) -> "WebClientUnitsPage":
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=cls.page_count(total, page_size),
        )


class WebClientOrdersPage(WebClientPage):
    data: list[WebClientOrderItem]

    @classmethod
    def create(
        cls,
        *,
        data: list[WebClientOrderItem],
        total: int,
        page: int,
        page_size: int,
    ) -> "WebClientOrdersPage":
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=cls.page_count(total, page_size),
        )
