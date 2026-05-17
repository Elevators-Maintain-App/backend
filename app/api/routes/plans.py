from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.schemas.plans import PlanCreate, PlanResponse, PlanUpdate
from app.schemas.subscriptions import AdminPlanRead
from app.services.plans import (
    FreePlanCannotBeDeactivatedError,
    InvalidPlanPayloadError,
    PlanAdminService,
    PlanCodeAlreadyExistsError,
    PlanHasActiveSubscriptionsError,
    PlanNotFoundError,
    SubscriptionStatusService,
)


router = APIRouter()


def _admin_plan_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PlanNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, PlanCodeAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, PlanHasActiveSubscriptionsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, FreePlanCannotBeDeactivatedError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, InvalidPlanPayloadError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "code": exc.code},
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": "Error al administrar planes.", "code": "PLAN_ADMIN_ERROR"},
    )


@router.get(
    "/admin/plans",
    response_model=list[AdminPlanRead],
)
async def list_admin_plans(
    include_inactive: bool = Query(False),
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPlanRead]:
    return await SubscriptionStatusService(db).list_plans(include_inactive=include_inactive)


@router.post(
    "/admin/plans",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_plan(
    payload: PlanCreate,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    try:
        return await PlanAdminService(db).create_plan(payload)
    except Exception as exc:
        raise _admin_plan_http_error(exc) from exc


@router.get(
    "/admin/plans/{plan_id}",
    response_model=PlanResponse,
)
async def get_admin_plan(
    plan_id: UUID,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    try:
        return await PlanAdminService(db).get_plan(plan_id)
    except Exception as exc:
        raise _admin_plan_http_error(exc) from exc


@router.patch(
    "/admin/plans/{plan_id}/deactivate",
    response_model=PlanResponse,
)
async def deactivate_admin_plan(
    plan_id: UUID,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    try:
        return await PlanAdminService(db).deactivate_plan(plan_id)
    except Exception as exc:
        raise _admin_plan_http_error(exc) from exc


@router.patch(
    "/admin/plans/{plan_id}",
    response_model=PlanResponse,
)
async def update_admin_plan(
    plan_id: UUID,
    payload: PlanUpdate,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    try:
        return await PlanAdminService(db).update_plan(plan_id, payload)
    except Exception as exc:
        raise _admin_plan_http_error(exc) from exc
