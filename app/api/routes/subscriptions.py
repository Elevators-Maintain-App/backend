from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, get_current_firebase_user, require_role
from app.db.session import get_db
from app.schemas.subscriptions import CompanySubscriptionStatusResponse, SubscriptionAssignRequest
from app.services.plans import (
    CompanyNotFoundError,
    InvalidSubscriptionPeriodError,
    PlanInactiveError,
    PlanNotFoundError,
    SubscriptionNotFoundError,
    SubscriptionStatusService,
)


router = APIRouter()


def _plan_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SubscriptionNotFoundError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "La compania no tiene una suscripcion activa.",
                "code": "NO_ACTIVE_SUBSCRIPTION",
            },
        )
    if isinstance(exc, CompanyNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, PlanNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, PlanInactiveError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "code": exc.code},
        )
    if isinstance(exc, InvalidSubscriptionPeriodError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "code": exc.code},
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": "Error al consultar la suscripcion.", "code": "SUBSCRIPTION_ERROR"},
    )


@router.get(
    "/subscription/me",
    response_model=CompanySubscriptionStatusResponse,
)
async def get_my_subscription(
    current_user: FirebaseUser = Depends(get_current_firebase_user),
    db: AsyncSession = Depends(get_db),
) -> CompanySubscriptionStatusResponse:
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "El usuario autenticado no tiene compania asociada.", "code": "COMPANY_NOT_FOUND"},
        )

    try:
        return await SubscriptionStatusService(db).get_company_status(current_user.company_id)
    except Exception as exc:
        raise _plan_http_error(exc) from exc


@router.get(
    "/admin/companies/{company_id}/subscription",
    response_model=CompanySubscriptionStatusResponse,
)
async def get_company_subscription(
    company_id: UUID,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> CompanySubscriptionStatusResponse:
    try:
        return await SubscriptionStatusService(db).get_company_status(company_id)
    except Exception as exc:
        raise _plan_http_error(exc) from exc


@router.post(
    "/admin/companies/{company_id}/subscription",
    response_model=CompanySubscriptionStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_company_subscription(
    company_id: UUID,
    payload: SubscriptionAssignRequest,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> CompanySubscriptionStatusResponse:
    try:
        return await SubscriptionStatusService(db).assign_subscription(company_id, payload)
    except Exception as exc:
        raise _plan_http_error(exc) from exc
