from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.firebase import FirebaseUser, require_role
from app.db.session import get_db
from app.schemas.web_superadmin import (
    WebSuperAdminUsersPage,
    WebSuperAdminUsersSummary,
)
from app.services.web_superadmin import WebSuperAdminService


router = APIRouter()

UserRoleFilter = Literal["technician", "supervisor", "admin", "superAdmin", "client"]


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
