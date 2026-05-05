from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.schemas.web_client import (
    WebClientDashboard,
    WebClientOrderDetail,
    WebClientOrdersPage,
    WebClientReportLink,
    WebClientUnitDetail,
    WebClientUnitsPage,
)
from app.services.web.client_dashboard_service import WebClientDashboardService
from app.services.web.client_portal_service import WebClientPortalService


router = APIRouter()


@router.get("/dashboard", response_model=WebClientDashboard)
async def get_client_dashboard(
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientDashboard:
    return await WebClientDashboardService(db).get_dashboard(current_user)


@router.get("/units", response_model=WebClientUnitsPage)
async def get_client_units(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    search: Annotated[str | None, Query()] = None,
    project_id: Annotated[UUID | None, Query()] = None,
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientUnitsPage:
    return await WebClientPortalService(db).get_units(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        project_id=project_id,
    )


@router.get("/units/{unit_id}", response_model=WebClientUnitDetail)
async def get_client_unit_detail(
    unit_id: UUID,
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientUnitDetail:
    return await WebClientPortalService(db).get_unit_detail(current_user, unit_id)


@router.get("/orders", response_model=WebClientOrdersPage)
async def get_client_orders(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    search: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    unit_id: Annotated[UUID | None, Query()] = None,
    project_id: Annotated[UUID | None, Query()] = None,
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientOrdersPage:
    return await WebClientPortalService(db).get_orders(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        status_name=status,
        unit_id=unit_id,
        project_id=project_id,
    )


@router.get("/orders/{order_id}", response_model=WebClientOrderDetail)
async def get_client_order_detail(
    order_id: UUID,
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientOrderDetail:
    return await WebClientPortalService(db).get_order_detail(current_user, order_id)


@router.get("/orders/{order_id}/report", response_model=WebClientReportLink)
async def get_client_order_report(
    order_id: UUID,
    current_user: FirebaseUser = Depends(require_role("client")),
    db: AsyncSession = Depends(get_db),
) -> WebClientReportLink:
    return await WebClientPortalService(db).get_order_report(current_user, order_id)
