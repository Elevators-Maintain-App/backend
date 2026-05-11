from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.db.models.usuarios import Rol
from app.schemas.web_superadmin import (
    WebSuperAdminCatalogItem,
    WebSuperAdminUsersPage,
    WebSuperAdminUsersSummary,
    WebUserCreate,
    WebUserDeleteResponse,
    WebUserDetail,
    WebUserDisableResponse,
    WebUserUpdate,
)
from app.services.web_superadmin import WebSuperAdminService


router = APIRouter()

UserRoleFilter = Literal["technician", "supervisor", "admin", "superAdmin", "client"]


async def _parse_web_user_create_payload(request: Request) -> WebUserCreate:
    content_type = request.headers.get("content-type", "")
    try:
        if "application/json" in content_type:
            payload = await request.json()
        else:
            form = await request.form()
            payload = dict(form)
        return WebUserCreate(**payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload invalido",
        ) from exc


@router.get(
    "/catalogs/roles",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_roles_catalog(
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
) -> list[WebSuperAdminCatalogItem]:
    return [
        WebSuperAdminCatalogItem(id=role.value, name=role.value)
        for role in Rol
    ]


@router.get(
    "/catalogs/companies",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_companies_catalog(
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_companies_catalog()


@router.get(
    "/catalogs/document-types",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_document_types_catalog(
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_document_types_catalog()


@router.get(
    "/catalogs/technical-levels",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_technical_levels_catalog(
    company_id: Annotated[UUID | None, Query()] = None,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_technical_levels_catalog(
        company_id=company_id,
    )


@router.get(
    "/companies/{company_id}/clients",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_company_clients_catalog(
    company_id: UUID,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_company_clients_catalog(
        company_id=company_id,
    )


@router.get(
    "/users/summary",
    response_model=WebSuperAdminUsersSummary,
)
async def get_users_summary(
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebSuperAdminUsersSummary:
    return await WebSuperAdminService(db).get_users_summary()


@router.get(
    "/users",
    response_model=WebSuperAdminUsersPage,
)
async def get_users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query()] = None,
    role: Annotated[UserRoleFilter | None, Query()] = None,
    company_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebSuperAdminUsersPage:
    return await WebSuperAdminService(db).get_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        company_id=company_id,
        status_value=status,
    )


@router.post(
    "/users",
    response_model=WebUserDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: Request,
    user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebUserDetail:
    payload = await _parse_web_user_create_payload(request)
    return await WebSuperAdminService(db).create_user(
        current_user=user,
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/users/{uid}",
    response_model=WebUserDetail,
)
async def get_user_detail(
    uid: str,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebUserDetail:
    return await WebSuperAdminService(db).get_user_detail(uid)


@router.patch(
    "/users/{uid}",
    response_model=WebUserDetail,
)
async def update_user(
    uid: str,
    payload: WebUserUpdate,
    _user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebUserDetail:
    return await WebSuperAdminService(db).update_user(uid, payload)


@router.post(
    "/users/{uid}/disable",
    response_model=WebUserDisableResponse,
)
async def disable_user(
    uid: str,
    user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebUserDisableResponse:
    return await WebSuperAdminService(db).disable_user(uid=uid, current_user=user)


@router.delete(
    "/users/{uid}",
    response_model=WebUserDeleteResponse,
)
async def delete_user(
    uid: str,
    user: FirebaseUser = Depends(require_role("superAdmin", "super_admin")),
    db: AsyncSession = Depends(get_db),
) -> WebUserDeleteResponse:
    return await WebSuperAdminService(db).delete_user(uid=uid, current_user=user)
