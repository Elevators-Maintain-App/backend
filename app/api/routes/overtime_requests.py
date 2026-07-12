from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status as http_status
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
    OvertimeRequestPage,
    OvertimeRequestSummary,
    OvertimeRequestUpdate,
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


@router.get("/requests/me/page", response_model=OvertimeRequestPage)
async def page_my_overtime_requests(
    status: OvertimeRequestStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).page_own_requests(
        current_user, status=status, date_from=date_from, date_to=date_to,
        page=page, page_size=page_size,
    )


@router.get("/requests/me/{request_id}", response_model=OvertimeRequestDetail)
async def get_my_overtime_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).get_own_request(current_user, request_id)


@router.patch("/requests/me/{request_id}", response_model=OvertimeRequestDetail)
async def update_my_overtime_request(
    request_id: UUID,
    payload: OvertimeRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).update_own_request(current_user, request_id, payload)


@router.post("/requests/me/{request_id}/cancel", response_model=OvertimeRequestDetail)
async def cancel_my_overtime_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("technician")),
):
    return await OvertimeRequestService(db).cancel_own_request(current_user, request_id)


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


@router.get("/supervisor/requests/page", response_model=OvertimeRequestPage)
async def page_supervisor_overtime_requests(
    status: OvertimeRequestStatus | None = Query(None),
    technician_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    return await OvertimeRequestService(db).page_assigned_requests(
        current_user, status=status, technician_id=technician_id,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size,
    )


@router.get(
    "/supervisor/requests/export",
    response_class=Response,
    responses={
        200: {
            "description": "Archivo binario PDF o XLSX según el formato solicitado",
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                    "schema": {"type": "string", "format": "binary"}
                },
            },
        }
    },
)
async def export_supervisor_overtime_requests(
    format: Literal["pdf", "xlsx"] = Query(...),
    status: OvertimeRequestStatus | None = Query(None),
    technician_id: UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: FirebaseUser = Depends(require_role("supervisor")),
):
    content, media_type, filename = await OvertimeRequestService(db).export_assigned_requests(
        current_user, export_format=format, status=status, technician_id=technician_id,
        date_from=date_from, date_to=date_to,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
