from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.web.superadmin_users import (
    WebUserCreate,
    WebUserDeleteResponse,
    WebUserDetail,
    WebUserDisableResponse,
    WebUserListItem,
    WebUserListResponse,
    WebUserUpdate,
)


class WebSuperAdminCatalogItem(BaseModel):
    id: str
    name: str


class WebSuperAdminUsersSummary(BaseModel):
    total_users: int = Field(..., ge=0)


WebSuperAdminUserItem = WebUserListItem
WebSuperAdminUsersPage = WebUserListResponse

__all__ = [
    "WebSuperAdminCatalogItem",
    "WebSuperAdminUserItem",
    "WebSuperAdminUsersPage",
    "WebSuperAdminUsersSummary",
    "WebUserCreate",
    "WebUserDeleteResponse",
    "WebUserDetail",
    "WebUserDisableResponse",
    "WebUserListItem",
    "WebUserListResponse",
    "WebUserUpdate",
]
