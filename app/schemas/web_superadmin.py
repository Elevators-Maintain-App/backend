from math import ceil
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WebSuperAdminCatalogItem(BaseModel):
    id: str
    name: str


class WebSuperAdminUsersSummary(BaseModel):
    total_users: int = Field(..., ge=0)


class WebSuperAdminUserItem(BaseModel):
    uid: str
    email: str
    display_name: str
    role: str
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: bool


class WebSuperAdminUsersPage(BaseModel):
    data: list[WebSuperAdminUserItem]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)

    @classmethod
    def create(
        cls,
        *,
        data: list[WebSuperAdminUserItem],
        total: int,
        page: int,
        page_size: int,
    ) -> "WebSuperAdminUsersPage":
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )
