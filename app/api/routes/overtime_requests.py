from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.models.overtime_requests import OvertimeRequestStatus
from app.db.session import get_db
from app.schemas.overtime_requests import (
    OvertimeAdjustAndApproveRequest,
    OvertimeApproveRequest,
    OvertimeCatalogItem,
    OvertimeRejectRequest,
    OvertimeRequestCreate,
    OvertimeRequestDetail,
    OvertimeRequestSummary,
)
from app.services.overtime.request_service import OvertimeRequestService


router = APIRouter()


@router.get("/catalogs/projects", response_model=list[OvertimeCatalogItem])
async def list_overtime_projects(
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).list_project_catalog(current_user)


@router.get("/catalogs/supervisors", response_model=list[OvertimeCatalogItem])
async def list_overtime_supervisors(
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).list_supervisor_catalog(current_user)


@router.post(
    "/requests",
    response_model=OvertimeRequestDetail,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_overtime_request(
    payload: OvertimeRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).create_request(current_user, payload)


@router.get("/requests/me", response_model=list[OvertimeRequestSummary])
async def list_my_overtime_requests(
    status: OvertimeRequestStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).list_own_requests(
        current_user, status=status, date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )


@router.get("/requests/me/{request_id}", response_model=OvertimeRequestDetail)
async def get_my_overtime_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).get_own_request(current_user, request_id)


@router.get("/supervisor/requests", response_model=list[OvertimeRequestSummary])
async def list_supervisor_overtime_requests(
    status: OvertimeRequestStatus | None = Query(None),
    technician_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).list_assigned_requests(
        current_user, status=status, technician_id=technician_id,
        date_from=date_from, date_to=date_to, skip=skip, limit=limit
    )


@router.get("/supervisor/requests/{request_id}", response_model=OvertimeRequestDetail)
async def get_supervisor_overtime_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).get_assigned_request(current_user, request_id)


@router.post("/supervisor/requests/{request_id}/approve", response_model=OvertimeRequestDetail)
async def approve_overtime_request(
    request_id: UUID,
    payload: OvertimeApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).approve(current_user, request_id, payload)


@router.post(
    "/supervisor/requests/{request_id}/adjust-and-approve",
    response_model=OvertimeRequestDetail,
)
async def adjust_and_approve_overtime_request(
    request_id: UUID,
    payload: OvertimeAdjustAndApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).adjust_and_approve(current_user, request_id, payload)


@router.post("/supervisor/requests/{request_id}/reject", response_model=OvertimeRequestDetail)
async def reject_overtime_request(
    request_id: UUID,
    payload: OvertimeRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).reject(current_user, request_id, payload)
