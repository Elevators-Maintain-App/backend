from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.db.models.usuarios import Rol
from app.schemas.usuarios import UsuarioOut
from app.schemas.web_superadmin import (
    WebSuperAdminCatalogItem,
    WebSuperAdminUsersPage,
    WebSuperAdminUsersSummary,
)
from app.services.usuario.usuarios import UsuarioService
from app.services.web_superadmin import WebSuperAdminService


router = APIRouter()

UserRoleFilter = Literal["technician", "supervisor", "admin", "superAdmin", "client"]


@router.get(
    "/catalogs/roles",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_roles_catalog(
    _user: FirebaseUser = Depends(require_role("superAdmin")),
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
    _user: FirebaseUser = Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_companies_catalog()


@router.get(
    "/catalogs/document-types",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_document_types_catalog(
    _user: FirebaseUser = Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
) -> list[WebSuperAdminCatalogItem]:
    return await WebSuperAdminService(db).get_document_types_catalog()


@router.get(
    "/catalogs/technical-levels",
    response_model=list[WebSuperAdminCatalogItem],
)
async def get_technical_levels_catalog(
    company_id: Annotated[UUID | None, Query()] = None,
    _user: FirebaseUser = Depends(require_role("superAdmin")),
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
    _user: FirebaseUser = Depends(require_role("superAdmin")),
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
    _user: FirebaseUser = Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
) -> WebSuperAdminUsersSummary:
    return await WebSuperAdminService(db).get_users_summary()


@router.get(
    "/users",
    response_model=WebSuperAdminUsersPage,
)
async def get_users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    search: Annotated[str | None, Query()] = None,
    role: Annotated[UserRoleFilter | None, Query()] = None,
    _user: FirebaseUser = Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
) -> WebSuperAdminUsersPage:
    return await WebSuperAdminService(db).get_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
    )


@router.post(
    "/users",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: Request,
    company_id: Annotated[UUID, Form()],
    display_name: Annotated[str, Form()],
    document_id: Annotated[str, Form()],
    document_type_id: Annotated[int, Form()],
    email: Annotated[str, Form()],
    phone_number: Annotated[str, Form()],
    rol: Annotated[UserRoleFilter, Form()],
    client_id: Annotated[UUID | None, Form()] = None,
    nivel: Annotated[str | None, Form()] = None,
    zona_geografica_id: Annotated[UUID | None, Form()] = None,
    is_active: Annotated[bool | None, Form()] = True,
    photo: Annotated[UploadFile | None, File()] = None,
    user: FirebaseUser = Depends(require_role("superAdmin")),
    db: AsyncSession = Depends(get_db),
) -> UsuarioOut:
    usuario_data = {
        "company_id": company_id,
        "display_name": display_name,
        "document_id": document_id,
        "document_type_id": document_type_id,
        "email": email,
        "phone_number": phone_number,
        "rol": Rol(rol),
        "client_id": client_id,
        "nivel": nivel,
        "zona_geografica_id": zona_geografica_id,
        "is_active": is_active,
    }
    return await UsuarioService(db).create(
        user,
        usuario_data,
        photo,
        request_id=getattr(request.state, "request_id", None),
    )
