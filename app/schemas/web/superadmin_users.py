from datetime import datetime
from math import ceil
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


WebUserRole = Literal["technician", "supervisor", "admin", "superAdmin", "client"]
WebUserStatus = Literal["active", "inactive", "unknown"]


class WebUserListItem(BaseModel):
    uid: str
    display_name: str
    email: str
    phone: str | None = None
    role: str
    company_id: UUID | None = None
    company_name: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None
    status: WebUserStatus = "unknown"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WebUserListResponse(BaseModel):
    items: list[WebUserListItem]
    # Backward-compatible alias for the current web frontend service.
    data: list[WebUserListItem]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)

    @classmethod
    def create(
        cls,
        *,
        items: list[WebUserListItem],
        total: int,
        page: int,
        page_size: int,
    ) -> "WebUserListResponse":
        return cls(
            items=items,
            data=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )


class WebUserDetail(WebUserListItem):
    id: UUID | None = None
    phone_number: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None
    document_id: str | None = None
    document_type_id: int | None = None
    document_type_name: str | None = None
    client_id: UUID | None = None
    nivel: str | None = None


class WebUserCreate(BaseModel):
    display_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str | None = None
    phone_number: str | None = None
    role: WebUserRole | None = None
    rol: WebUserRole | None = None
    company_id: UUID | None = None
    password: str | None = Field(default=None, min_length=6)
    document_id: str | None = None
    document_type_id: int | None = None
    client_id: UUID | None = None
    nivel: str | None = None
    is_active: bool | None = True


class WebUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    phone_number: str | None = None
    role: WebUserRole | None = None
    rol: WebUserRole | None = None
    company_id: UUID | None = None
    status: Literal["active", "inactive"] | None = None
    is_active: bool | None = None


class WebUserDisableResponse(BaseModel):
    uid: str
    status: Literal["inactive"]
    message: str


class WebUserDeleteResponse(BaseModel):
    uid: str
    deleted: bool
    message: str
